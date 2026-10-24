"""speech_only.wav: the voice runs of mic16k.wav joined with 0.6 s gaps, plus speech_map.json
([[pos_in_speech_only, source_start, length], ...]) to map transcript times back to the recording."""
import wave, json, sys, numpy as np
end = float(sys.argv[sys.argv.index("--end") + 1]) if "--end" in sys.argv else 1e9
sil, s = [], None
for line in open("silences_vad.txt"):
    k, v = line.split(); v = float(v)
    if k.startswith("silence_start"): s = v
    elif s is not None: sil.append((s, v)); s = None
w = wave.open("mic16k.wav"); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
dur = len(x) / sr
keep, cur = [], 0.0
for a, b in sil:
    if a >= end: break
    if a > cur: keep.append((cur, min(a, end)))
    cur = b
if cur < min(end, dur): keep.append((cur, min(end, dur)))
gap = np.zeros(int(sr * 0.6), np.int16)
parts, mp, pos = [], [], 0.0
for a, b in keep:
    seg = x[int(a * sr):int(b * sr)]
    mp.append([round(pos, 3), round(a, 3), round(b - a, 3)])
    parts += [seg, gap]; pos += len(seg) / sr + 0.6
y = np.concatenate(parts)
o = wave.open("speech_only.wav", "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes(y.tobytes()); o.close()
json.dump(mp, open("speech_map.json", "w"))
print(f"{len(keep)} voice runs, {len(y)/sr/60:.1f} min to transcribe")
