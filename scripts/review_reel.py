"""A 2–4 minute review reel of the finished video's riskiest and most designed moments, for a phone check.

Run inside <project>/work after the render:  review_reel.py ../renders/<name>.mp4
Takes: the intro's last 6 s (title), the name lower-third, every chapter card, explainer and prompt card, the
first fast-forwards, the moments with the most privacy blurs (fast scrolls are where leaks happened), and the
start of the end screen. Writes ../renders/review_reel.mp4 (1280x720) and review_reel.txt — what each clip is
and where it sits in the full video, so feedback like "clip 7 looks off" maps to a timestamp.
"""
import json, os, re, subprocess, sys

render = sys.argv[1]
INTRO = float(re.search(r'id="intro"[^>]*data-duration="([\d.]+)"', open("../index.html").read()).group(1))
edl = json.load(open("edl.json")); TOTAL = edl["total"]
load = lambda f: json.load(open(f)) if os.path.exists(f) else []

picks = [(max(0, INTRO - 6), 6, "intro title")]
body = open("../compositions/body.html").read()
m = re.search(r'id="bd-lt"[^>]*data-start="([\d.]+)"', body)
if m:
    picks.append((INTRO + float(m.group(1)) - 0.3, 4, "name lower-third"))
for c in load("chapters.json"):
    picks.append((INTRO + c["t"] - 0.3, 4.5, f'chapter: {c["title"]}'))
for e in load("explainers.json"):
    picks.append((INTRO + e["t"] - 0.3, min(e["d"], 8) + 0.6, f'explainer ({e.get("kind", "headline")}): {e.get("title", "")[:40]}'))
for p in load("prompts.json"):
    picks.append((INTRO + p["t"] - 0.3, min(p["d"], 6) + 0.6, "prompt card"))
for f in [f for f in edl["ffwd"] if f["d"] > 1][:2]:
    picks.append((INTRO + f["t"] - 1, f["d"] + 2, f'fast-forward {f["x"]}x'))
# privacy: the 4 body seconds with the most blur boxes (OCR samples every 5 frames)
if os.path.exists("ocr/body.jsonl"):
    counts = {}
    for line in open("ocr/body.jsonl"):          # parts were OCR'd in parallel: the frame number is in the name
        try:
            r = json.loads(line)
        except ValueError:
            continue
        n = len(r.get("m", []))
        sec = int(int(os.path.basename(r["f"]).split(".")[0]) * 5 / edl["fps"])
        counts[sec] = counts.get(sec, 0) + n
    chosen = []
    for sec, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if len(chosen) == 8:
            break
        if all(abs(sec - c) >= 30 for c in chosen):       # spread over the video, not one busy scroll
            chosen.append(sec)
            picks.append((INTRO + sec - 1.5, 4, f"privacy check: {n} blurred items"))
picks.append((INTRO + TOTAL - 0.5, 6, "end screen"))

picks.sort()
merged = []
for t, d, why in picks:                       # overlapping picks become one clip
    if merged and t < merged[-1][0] + merged[-1][1]:
        a, d0, w0 = merged[-1]
        merged[-1] = (a, max(d0, t + d - a), w0 + " + " + why)
    else:
        merged.append((t, d, why))

def ts(x):
    x = int(x); return f"{x // 3600}:{x % 3600 // 60:02d}:{x % 60:02d}"

parts = []
for i, (t, d, why) in enumerate(merged):
    out = f"reel_{i:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", f"{d:.2f}", "-i", render,
                    "-vf", "scale=1280:720,fps=25", "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2", out], check=True)
    parts.append(out)
open("reel_list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "reel_list.txt", "-c", "copy",
                "../renders/review_reel.mp4"], check=True)
for p in parts:
    os.remove(p)
pos, lines = 0.0, []
for i, (t, d, why) in enumerate(merged, 1):
    lines.append(f"{i:2d}. reel {ts(pos)}  →  video {ts(t)}   {why}")
    pos += d
open("../renders/review_reel.txt", "w").write("\n".join(lines) + "\n")
print(f"review_reel.mp4: {len(merged)} clips, {pos / 60:.1f} min"); print("\n".join(lines))
