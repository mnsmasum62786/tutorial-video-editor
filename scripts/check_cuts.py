"""Every place the voice track is cut (a jump in source time, or the start/end of a muted fast-forward)
must sit in silence: RMS of the 40 ms on the kept side of the cut below the silence threshold."""
import json, sys, wave, numpy as np
w = wave.open("mic16k.wav"); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def db(t0, t1):
    s = x[max(0, int(t0 * sr)):int(t1 * sr)]
    return -120 if len(s) == 0 else 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9)
segs = json.load(open("edl.json"))["segs"]
FPS, W, THR = 25, 0.04, -38
bad = []
for i in range(len(segs) - 1):
    a, b = segs[i], segs[i + 1]
    if a["k"] == 1 and (b["a"] != a["b"] or b["k"] != 1):        # audio ends here
        lvl = db(a["b"] / FPS - W, a["b"] / FPS)
        if lvl > THR: bad.append(("end", a["b"] / FPS, round(lvl, 1)))
    if b["k"] == 1 and (b["a"] != a["b"] or a["k"] != 1):        # audio starts here
        lvl = db(b["a"] / FPS, b["a"] / FPS + W)
        if lvl > THR: bad.append(("start", b["a"] / FPS, round(lvl, 1)))
print(f"{len(segs)} segments, {len(bad)} cut points above {THR} dB")
for k, t, l in bad[:25]:
    print(f"  {k:5s} at source {int(t//60):02d}:{t%60:05.2f}  {l} dB")
if bad:
    sys.exit(f"{len(bad)} cut points land on sound — fix edl.json before rendering")
