"""PRIVACY_REPORT.md: what was blurred, how often, and where — so he can trust (or spot-check) the render.

Run inside <project>/work after the blur stage. Values are masked in the report itself (first 3 characters +
length), because the report may be shared or pasted into a chat.
"""
import json, os, re

edl = json.load(open("edl.json")); FPS = edl["fps"]
INTRO = float(re.search(r'id="intro"[^>]*data-duration="([\d.]+)"', open("../index.html").read()).group(1))

def mask(v):
    v = v.strip()
    return (v[:3] + "…" + f"({len(v)})") if len(v) > 4 else "•••"

def ts(x):
    x = int(x); return f"{x // 3600}:{x % 3600 // 60:02d}:{x % 60:02d}"

kinds = {}
for src, step, offset in (("ocr/body.jsonl", 5, INTRO), ("ocr/intro.jsonl", 1, 0.0)):
    if not os.path.exists(src):
        continue
    for line in open(src):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        t = offset + int(os.path.basename(r["f"]).split(".")[0]) * step / FPS
        for box in r.get("m", []):
            kind, text = box[4], box[5] if len(box) > 5 else ""
            k = kinds.setdefault(kind, {"n": 0, "values": {}, "first": t, "last": t})
            k["n"] += 1; k["first"] = min(k["first"], t); k["last"] = max(k["last"], t)
            mv = mask(text)
            k["values"][mv] = k["values"].get(mv, 0) + 1

lines = ["# Privacy report", "",
         "Every item below was blurred in the final video (times are in the final video). Values are masked here.", "",
         "| What | Blurred (samples) | Distinct values | First seen | Last seen |", "|---|---|---|---|---|"]
for kind, k in sorted(kinds.items(), key=lambda kv: -kv[1]["n"]):
    top = ", ".join(f"`{v}`" for v, _ in sorted(k["values"].items(), key=lambda kv: -kv[1])[:4])
    lines.append(f"| {kind} | {k['n']} | {len(k['values'])} ({top}) | {ts(k['first'])} | {ts(k['last'])} |")
lines += ["", "Also covered without OCR: the browser tab/address bar (cropped off), the bottom edge strip (28 px), "
          "the client contact's profile photo next to their name.",
          "Not covered automatically: things on his camera (papers, phone, a monitor behind him) and anything spoken "
          "aloud — check those by watching the review reel."]
open("../PRIVACY_REPORT.md", "w").write("\n".join(lines) + "\n")
print(f"PRIVACY_REPORT.md: {sum(k['n'] for k in kinds.values())} blurred samples in {len(kinds)} categories")
