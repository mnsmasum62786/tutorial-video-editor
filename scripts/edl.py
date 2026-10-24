"""Build the body edit from speech pauses + screen activity (+ optional transcript hints).

Everything is in source frames at 25 fps, so video (frame select) and audio (sample slices)
cut at identical points and can never drift.

Output: edl.json with
  segs:   [{a, b, k}]  source frames [a, b), keep every k-th frame (k=1 normal speed)
  shots:  [{t, mode}]  output seconds where the layout switches ("screen" | "face")
  zooms:  [{t, s, x, y}] output seconds, zoom scale and focus (0..1 of the content area)
  ffwd:   [{t, d, x}] fast-forward badges: output start, output length, speed multiple
"""
import json, sys, math

FPS = 25
END_S = float(sys.argv[1]) if len(sys.argv) > 1 else 5040.0  # body end (source seconds)
START_S = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
CHROME = 0.112          # browser tabs + bookmarks bar, cropped off the screen recording
ACT = 0.0008            # a half-second counts as "screen moving" above this changed fraction

# ---------- inputs ----------
sil = []
s = None
for line in open("silences_safe.txt"):
    k, v = line.split()
    v = float(v)
    if k.startswith("silence_start"):
        s = v
    elif s is not None:
        sil.append((s, v)); s = None

act = {}
for line in open("activity.jsonl"):
    r = json.loads(line)
    act[round(r["t"] * 2)] = r

def frac(t):
    return act.get(round(t * 2), {}).get("frac", 0.0)

def active_share(a, b, thr=ACT):
    n = max(1, int((b - a) * 2))
    return sum(1 for i in range(n) if frac(a + i / 2) > thr) / n

REAL = 0.004            # a real screen change (page, scroll, typing), not just the cursor

# ---------- 1. segments ----------
speech = []
cur = START_S
for a, b in sil:
    if b <= START_S or a >= END_S:
        continue
    if a > cur:
        speech.append((cur, min(a, END_S)))
    cur = max(cur, b)
if cur < END_S:
    speech.append((cur, END_S))

# content cuts (retakes, repeats, lines the intro already used): hints.json "cut": [[a, b], ...]
try:
    _cuts = json.load(open("hints.json")).get("cut", [])
except FileNotFoundError:
    _cuts = []
for ca, cb in _cuts:
    out = []
    for a, b in speech:
        if b <= ca or a >= cb:
            out.append((a, b))
        else:
            if a < ca: out.append((a, ca))
            if b > cb: out.append((cb, b))
    speech = out

f = lambda t: int(round(t * FPS))
segs = []

def add(a, b, k=1):
    a, b = f(a), f(b)
    if b - a < 1:
        return
    if segs and segs[-1]["k"] == k == 1 and segs[-1]["b"] == a:
        segs[-1]["b"] = b
    else:
        segs.append({"a": a, "b": b, "k": k})

# every cut snaps to the quietest 40 ms (on 1/25 s frame boundaries) near where it would go;
# a pause with no quiet moment is not cut at all, so a cut can never clip a word
import wave, numpy as np
_w = wave.open("mic16k.wav"); _sr = _w.getframerate()
_x = np.frombuffer(_w.readframes(_w.getnframes()), np.int16).astype(np.float32) / 32768
QUIET = -40.0
def level(t0, t1):
    seg = _x[max(0, int(t0 * _sr)):int(t1 * _sr)]
    return -120.0 if len(seg) == 0 else float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
def quiet_end(lo, hi):     # audio kept up to c: the 40 ms before c must be quiet
    best = None
    for fr in range(int(np.ceil(lo * FPS)), int(hi * FPS) + 1):
        c = fr / FPS; l = level(c - 0.04, c)
        if best is None or l < best[1]: best = (c, l)
    return best[0] if best and best[1] <= QUIET else None
def quiet_start(lo, hi):   # audio resumes at c: the 40 ms after c must be quiet
    best = None
    for fr in range(int(np.ceil(lo * FPS)), int(hi * FPS) + 1):
        c = fr / FPS; l = level(c, c + 0.04)
        if best is None or l < best[1]: best = (c, l)
    return best[0] if best and best[1] <= QUIET else None

kept_unsafe = 0
for i, (a, b) in enumerate(speech):
    add(a, b)
    if i + 1 == len(speech):
        break
    na = speech[i + 1][0]
    gap = na - b
    if gap <= 0.55:
        add(b, na)
        continue
    share = active_share(b, na, REAL)
    crosses_cut = any(b <= ca and cb <= na for ca, cb in _cuts)
    mid = (b + na) / 2
    ce = quiet_end(b + 0.08, min(b + 0.6, mid))
    cs = quiet_start(max(na - 0.6, mid), na - 0.08)
    if ce is None or cs is None or cs <= ce:   # nowhere quiet to cut: keep the whole pause
        add(b, na); kept_unsafe += 1
        continue
    if crosses_cut or share < 0.35:        # a content cut, or a still screen: close the gap
        add(b, ce); add(cs, na)
    elif gap <= 1.2:                       # short action: keep at speed
        add(b, na)
    elif cs - ce <= 1.4:                   # a little longer: keep the action at 2x (muted)
        add(b, ce); add(ce, cs, 2); add(cs, na)
    else:                                  # long wait with the screen working: fast-forward (muted)
        add(b, ce)
        target = min(6.0, max(1.6, (cs - ce) / 4))
        k = max(2, int(round((cs - ce) / target)))
        add(ce, cs, k)
        add(cs, na)
print(f"pauses kept whole (no quiet point to cut): {kept_unsafe}")

# ---------- output time map ----------
def out_len(sg):
    n = sg["b"] - sg["a"]
    return math.ceil(n / sg["k"])

t = 0
for sg in segs:
    sg["t"] = t
    sg["n"] = out_len(sg)
    t += sg["n"]
TOTAL = t / FPS

def src_at(out_s):
    fr = out_s * FPS
    for sg in segs:
        if sg["t"] <= fr < sg["t"] + sg["n"]:
            return (sg["a"] + (fr - sg["t"]) * sg["k"]) / FPS
    return segs[-1]["b"] / FPS

# ---------- 2. layout: face when the screen (even the cursor) sits still while he talks ----------
hints = {}
try:
    hints = json.load(open("hints.json"))  # {"face": [[a,b]...], "screen": [[a,b]...]} source secs
except FileNotFoundError:
    pass

def forced(src, kind):
    return any(a <= src < b for a, b in hints.get(kind, []))

modes = []
for i in range(int(TOTAL * 2)):
    o = i / 2
    src = src_at(o)
    still = active_share(max(0, src - 4), src + 4) < 0.06
    m = "face" if still else "screen"
    if forced(src, "face"): m = "face"
    if forced(src, "screen"): m = "screen"
    modes.append(m)

# a face shot must last 6 s, a screen shot 3 s; shorter runs join their neighbour
def runs(ms):
    out = []
    for i, m in enumerate(ms):
        if out and out[-1][0] == m:
            out[-1][2] = i + 1
        else:
            out.append([m, i, i + 1])
    return out

for _ in range(3):
    rs = runs(modes)
    for m, a, b in rs:
        short = (b - a) / 2 < (6 if m == "face" else 3)
        if short:
            other = "screen" if m == "face" else "face"
            for i in range(a, b):
                modes[i] = other

shots = [{"t": a / 2, "mode": m} for m, a, b in runs(modes)]

# ---------- 3. zooms on where the screen changes ----------
def box_union(a, b):
    xs0, ys0, xs1, ys1, n = 1, 1, 0, 0, 0
    for i in range(int(a * 2), int(b * 2) + 1):
        r = act.get(i)
        if not r or r.get("frac", 0) <= ACT or "box" not in r:
            continue
        x0, y0, x1, y1 = r["box"]
        x0, x1 = x0 / 640, x1 / 640
        y0, y1 = (y0 / 374 - CHROME) / (1 - CHROME), (y1 / 374 - CHROME) / (1 - CHROME)
        if y1 < 0:   # change only in the browser chrome
            continue
        xs0, ys0 = min(xs0, x0), min(ys0, max(0, y0))
        xs1, ys1 = max(xs1, x1), max(ys1, y1)
        n += 1
    if n == 0:
        return None
    return xs0, ys0, xs1, ys1

zooms = []
STEP = 3.0
o = 0.0
last = (1.0, 0.5, 0.5)
while o < TOTAL:
    idx = min(len(modes) - 1, int(o * 2))
    want = (1.0, 0.5, 0.5)
    seg_k = next((sg["k"] for sg in segs if sg["t"] <= o * FPS < sg["t"] + sg["n"]), 1)
    if modes[idx] == "screen" and seg_k == 1:
        src = src_at(o)
        bx = box_union(src - 1.0, src + STEP + 1.0)
        if bx:
            x0, y0, x1, y1 = bx
            w, h = max(0.02, x1 - x0), max(0.02, y1 - y0)
            if w * h < 0.30:
                sc = min(1.7, 0.85 / max(w, h * 1.0))
                if sc >= 1.25:
                    sc = round(min(1.7, max(1.3, sc)), 2)
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    half = 0.5 / sc            # keep the zoomed view inside the content
                    cx = min(1 - half, max(half, cx)); cy = min(1 - half, max(half, cy))
                    want = (sc, round(cx, 3), round(cy, 3))
    # only move when the target changes enough; keep each framing at least STEP seconds
    if abs(want[0] - last[0]) > 0.15 or abs(want[1] - last[1]) > 0.12 or abs(want[2] - last[2]) > 0.12:
        zooms.append({"t": round(o, 2), "s": want[0], "x": want[1], "y": want[2]})
        last = want
    o += STEP

ffwd = [{"t": round(sg["t"] / FPS, 2), "d": round(sg["n"] / FPS, 2), "x": sg["k"]} for sg in segs if sg["k"] > 1]

json.dump({"fps": FPS, "total": round(TOTAL, 2), "segs": segs, "shots": shots, "zooms": zooms, "ffwd": ffwd},
          open("edl.json", "w"))
src_total = (segs[-1]["b"] - segs[0]["a"]) / FPS
face = sum(1 for m in modes if m == "face") / 2
print(f"source {src_total/60:.1f} min -> output {TOTAL/60:.1f} min | segments {len(segs)} | "
      f"fast-forwards {len(ffwd)} | shots {len(shots)} (face {face/60:.1f} min) | zoom moves {len(zooms)}")
