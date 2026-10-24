"""Candidate retakes: a sentence said, then said again soon after (he restarted it).

  python find_retakes.py [window_seconds=90]

Compares transcript lines within the window; similar text = the earlier take is a candidate cut
[earlier.s, later.s]. The Bengali transcript is rough — treat these as leads: re-transcribe both
pieces (or look at the screen) before adding a cut to hints.json, and never cut what you can't confirm.
Writes retakes.json and prints them.
"""
import json, sys, difflib, re
W = float(sys.argv[1]) if len(sys.argv) > 1 else 90
rows = json.load(open("transcript_src.json"))
norm = lambda t: re.sub(r"[\s,।.?!\-]+", "", t.lower())
def loop(t):            # whisper repetition loops are not speech
    w = t.split()
    return len(w) > 6 and len(set(w)) < len(w) * 0.35
out = []
for i, a in enumerate(rows):
    na = norm(a["text"])
    if len(na) < 14 or loop(a["text"]): continue
    for b in rows[i + 1:]:
        if b["s"] - a["s"] > W: break
        if b["s"] - a["s"] < 4: continue          # whisper re-emitting one line, not a second take
        nb = norm(b["text"])
        if len(nb) < 14: continue
        r = difflib.SequenceMatcher(None, na, nb).ratio()
        if r >= 0.62:
            out.append({"cut": [a["s"], b["s"]], "ratio": round(r, 2), "first": a["text"][:90], "again": b["text"][:90]})
            break
json.dump(out, open("retakes.json", "w"), ensure_ascii=False, indent=1)
for o in out:
    print(f"{o['cut'][0]/60:6.2f}–{o['cut'][1]/60:6.2f} min  r={o['ratio']}  {o['first'][:50]} | {o['again'][:50]}")
print(len(out), "candidates -> retakes.json")
