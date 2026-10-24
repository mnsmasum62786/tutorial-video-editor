"""Render an edit list (edl.json segs) into frame-exact media.

  python render_media.py <edl.json> <out_prefix> [cam|screen|voice ...]

Video: one ffmpeg pass per source with a frame-index select expression (every source frame
is either kept or dropped, fast-forwards keep every k-th frame), so output frame i maps to
exactly one source frame. Voice: the same frame ranges sliced as audio samples (1920 samples
per frame at 48 kHz), fast-forwards become silence, 4 ms fades on every cut.
"""
import json, sys, subprocess, wave, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SRC = os.environ.get("TVE_SRC") or sys.exit("set TVE_SRC to the recording prefix, e.g. '/path/My talk_' (…_Camera.mp4, …_Screen.mp4, …_Microphone.mp3)")
FPS = 25
SR = 48000
SPF = SR // FPS

edl = json.load(open(sys.argv[1]))
out = sys.argv[2]
which = sys.argv[3:] or ["cam", "screen", "voice"]
segs = edl["segs"]
total = sum(s["n"] for s in segs)

CHUNK = 80   # ffmpeg's expression parser fails on ~1000 terms, so render in chunks and join

def count_frames(path):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
                               "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path],
                              capture_output=True, text=True).stdout.strip())

def render_chunk(kind, ci, chunk):
    src = SRC + ("Camera.mp4" if kind == "cam" else "Screen.mp4")
    a0, b1 = chunk[0]["a"], chunk[-1]["b"]
    terms = []
    for s in chunk:   # frame n counts from the seek point a0
        a, b, k = s["a"] - a0, s["b"] - a0 - 1, s["k"]
        terms.append(f"between(n,{a},{b})" if k == 1 else f"between(n,{a},{b})*not(mod(n-{a},{k}))")
    vf = f"select='{'+'.join(terms)}',setpts=N/{FPS}/TB"
    if kind == "screen":   # drop the browser tabs + bookmarks bar, keep a sharp source for zooms
        vf += ",crop=3420:1772:0:224,scale=2560:1326:flags=lanczos"
    script = f"chunks/{out}_{kind}_{ci:03d}.vf"
    open(script, "w").write(vf)
    path = f"chunks/{out}_{kind}_{ci:03d}.mp4"
    br = "18M" if kind == "screen" else "10M"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-hwaccel", "videotoolbox", "-ss", f"{a0 / FPS:.3f}",
                    "-to", f"{b1 / FPS:.3f}", "-i", src, "-/vf", script, "-an", "-r", str(FPS),
                    "-c:v", "h264_videotoolbox", "-b:v", br, "-g", str(FPS), "-pix_fmt", "yuv420p", path],
                   check=True)
    want = sum(s["n"] for s in chunk)
    got = count_frames(path)
    if got != want:
        raise SystemExit(f"{kind} chunk {ci}: {got} frames, expected {want}")
    return path

def render_video(kind):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs("chunks", exist_ok=True)
    chunks = [segs[i:i + CHUNK] for i in range(0, len(segs), CHUNK)]
    with ThreadPoolExecutor(3) as ex:
        paths = list(ex.map(lambda ic: render_chunk(kind, *ic), enumerate(chunks)))
    lst = f"chunks/{out}_{kind}.txt"
    open(lst, "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in paths))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", f"{out}_{kind}.mp4"], check=True)
    print(f"{kind}: {count_frames(f'{out}_{kind}.mp4')} frames (expected {total})")

def render_voice():
    raw = "mic48.f32"
    if not os.path.exists(raw):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC + "Microphone.mp3", "-ac", "1",
                        "-ar", str(SR), "-f", "f32le", raw], check=True)
    x = np.memmap(raw, np.float32, "r")
    y = np.zeros(total * SPF, np.float32)
    fade = np.linspace(0, 1, int(SR * 0.004), dtype=np.float32)
    pos = 0
    for s in segs:
        n = s["n"] * SPF
        if s["k"] == 1:
            piece = np.array(x[s["a"] * SPF: s["a"] * SPF + n], np.float32)
            piece = np.pad(piece, (0, n - len(piece)))
            piece[:len(fade)] *= fade
            piece[-len(fade):] *= fade[::-1]
            y[pos:pos + n] = piece
        pos += n
    pcm = np.clip(y * 32767, -32768, 32767).astype(np.int16)
    tmp = f"{out}_voice_raw.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    from voice_chain import finish_voice        # clean + -14 LUFS, shared with the intro clips
    I, gain = finish_voice(tmp, f"{out}_voice.wav", SR)
    os.remove(tmp)
    print(f"voice: {total * SPF / SR:.2f}s, measured {I:.1f} LUFS, gain {gain:+.1f} dB")

for w in which:
    render_voice() if w == "voice" else render_video(w)
