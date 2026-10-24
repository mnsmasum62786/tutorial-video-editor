"""Pauses that are safe to cut: never inside a word.

- true silence from the level detector (silences_dB.txt: below -38 dB for 0.35 s+), and
- voice-free stretches of 3 s+ from the voice detector (typing, waiting) — long enough that no
  word can hide in them.
Writes silences_safe.txt in the same silencedetect format.
"""
def load(p):
    out, s = [], None
    for line in open(p):
        k, v = line.split(); v = float(v)
        if k.startswith("silence_start"): s = v
        elif s is not None: out.append((s, v)); s = None
    return out

db = load("silences_dB.txt")
vad = [(a, b) for a, b in load("silences_vad.txt") if b - a >= 3.0]
iv = sorted(db + vad)
merged = []
for a, b in iv:
    if merged and a <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], b)
    else:
        merged.append([a, b])
with open("silences_safe.txt", "w") as f:
    for a, b in merged:
        f.write(f"silence_start: {a:.3f}\nsilence_end: {b:.3f}\n")
tot = lambda L: sum(b - a for a, b in L) / 60
print(f"dB silences {tot(db):.1f} min, long voice-free {tot(vad):.1f} min, union {tot(merged):.1f} min")
