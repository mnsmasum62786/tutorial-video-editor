"""Map whisper-cli output (logs of speech_only.wav) back to recording time.

  python merge_tx.py tx_speech.log [more.log ...]

Writes transcript_src.json ([{"s", "e", "text"}]) and transcript_src.txt (mm:ss  text).
Lines that are whisper loops (the same word over and over) are dropped.
"""
import json, re, sys, bisect
mp = json.load(open("speech_map.json"))
starts = [m[0] for m in mp]
def to_src(t):
    i = max(0, bisect.bisect_right(starts, t) - 1)
    pos, a, d = mp[i]
    return a + min(max(0, t - pos), d)
rows = []
for path in sys.argv[1:]:
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\]\s*(.*)", line)
        if not m: continue
        g = m.groups()
        s = int(g[0]) * 3600 + int(g[1]) * 60 + float(g[2])
        e = int(g[3]) * 3600 + int(g[4]) * 60 + float(g[5])
        text = g[6].replace("�", "").strip()
        words = text.split()
        if not text or (len(words) > 6 and len(set(words)) < len(words) * 0.35): continue
        rows.append((to_src(s), to_src(max(s, e)), text))
rows.sort()
clean = []
for s, e, t in rows:
    if clean and t == clean[-1]["text"]: continue
    clean.append({"s": round(s, 2), "e": round(e, 2), "text": t})
json.dump(clean, open("transcript_src.json", "w"), ensure_ascii=False, indent=0)
with open("transcript_src.txt", "w") as f:
    for r in clean:
        f.write(f"{int(r['s']//60):02d}:{r['s']%60:05.2f}  {r['text']}\n")
print(len(clean), "lines", f"(last at {clean[-1]['s']/60:.1f} min)" if clean else "")
