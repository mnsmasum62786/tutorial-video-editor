"""Voice activity from the mic: tonal energy in the speech band, keyboard clicks filtered out.
Writes silences.txt in ffmpeg silencedetect format so edl.py can use it unchanged."""
import sys, wave, numpy as np

src = sys.argv[1] if len(sys.argv) > 1 else "mic16k.wav"
w = wave.open(src)
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
HOP, WIN = 320, 640                      # 20 ms hop, 40 ms window at 16 kHz
n = (len(x) - WIN) // HOP
idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
win = np.hanning(WIN).astype(np.float32)
voiced = np.zeros(n, bool)
energy = np.zeros(n, np.float32)
flat = np.zeros(n, np.float32)
freqs = np.fft.rfftfreq(WIN, 1 / sr)
band = (freqs > 120) & (freqs < 3500)
for c in range(0, n, 20000):              # chunked to keep memory small
    fr = x[idx[c:c + 20000]] * win
    sp = np.abs(np.fft.rfft(fr, axis=1))[:, band] + 1e-9
    e = (sp ** 2).sum(1)
    fl = np.exp(np.log(sp).mean(1)) / sp.mean(1)   # spectral flatness: ~1 noise, low for voice
    energy[c:c + 20000] = 10 * np.log10(e + 1e-12)
    flat[c:c + 20000] = fl

floor = np.percentile(energy[energy > -90], 20)
voiced = (energy > floor + 12) & (flat < 0.32)

def median(v, k):
    pad = np.pad(v.astype(np.int8), k // 2, mode="edge")
    s = np.lib.stride_tricks.sliding_window_view(pad, k)
    return np.median(s, 1) > 0.5

voiced = median(voiced, 9)                 # 180 ms: drops isolated clicks

# segments, merge gaps < 0.25 s, drop blips < 0.2 s
segs = []
start = None
for i, v in enumerate(voiced):
    if v and start is None: start = i
    if not v and start is not None: segs.append([start, i]); start = None
if start is not None: segs.append([start, n])
merged = []
for a, b in segs:
    if merged and (a - merged[-1][1]) * 0.02 < 0.25:
        merged[-1][1] = b
    else:
        merged.append([a, b])
merged = [(a * 0.02, b * 0.02 + 0.02) for a, b in merged if (b - a) * 0.02 >= 0.2]
PAD = 0.15                                 # keep word onsets and soft endings (s, sh, breathy vowels)
padded = []
for a, b in merged:
    a, b = max(0, a - PAD), b + PAD
    if padded and a - padded[-1][1] < 0.3:
        padded[-1][1] = b
    else:
        padded.append([a, b])
merged = [(a, b) for a, b in padded]

with open(sys.argv[2] if len(sys.argv) > 2 else "silences.txt", "w") as out:
    prev = 0.0
    for a, b in merged:
        if a - prev >= 0.3:
            out.write(f"silence_start: {prev:.3f}\nsilence_end: {a:.3f}\n")
        prev = b
    out.write(f"silence_start: {prev:.3f}\nsilence_end: {len(x)/sr:.3f}\n")
speech = sum(b - a for a, b in merged)
print(f"floor {floor:.1f} dB | speech {speech/60:.1f} min in {len(merged)} runs")
