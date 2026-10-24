"""Caption draft for a talking-head video, timed to the finished voice (assets/body_voice.wav).

Run inside <project>/work after build_all.sh's media stage. Writes captions_draft.json:
  [{"t": 3.2, "d": 2.4, "text": "…"}]   output seconds, one short phrase each (≤ ~42 characters, ≤ 2 lines)

Whisper's Bengali is phonetic and often misspelled, so the draft is NOT shippable: rewrite each line in correct
Bengali (keep his English tech words in English), mark one key word per few lines with **…** for the accent
colour, keep the times, and save as captions.json. Then show him the list (or a review reel) before rendering —
wrong words on screen are worse than no captions. Only for talking-head videos (no captions in screen-share
tutorials — his rule).
"""
import json, os, re, subprocess

MODEL = os.path.expanduser("~/.cache/hyperframes/whisper/models/ggml-large-v3.bin")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "../assets/body_voice.wav", "-ac", "1", "-ar", "16000",
                "cap16k.wav"], check=True)
# Whisper loops on long Bengali audio ("এই এই এই…" for a minute), even with pauses removed. So: cut the voice at
# its pauses into 2–9 s pieces and transcribe each piece on its own — a loop can't spread past one piece, and
# each caption is timed by real speech boundaries. The loop guards (-mc 0 -bs 1 -bo 1 -nf) as in transcribe.sh.
err = subprocess.run(["ffmpeg", "-hide_banner", "-i", "cap16k.wav", "-af", "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "cap16k.wav"],
                           capture_output=True, text=True).stdout)
gaps = list(zip(starts, ends))                      # (silence start, silence end)
speech, cur = [], 0.0
for s0, e0 in gaps:
    if s0 > cur + 0.05:
        speech.append([cur, s0])
    cur = e0
if cur < dur - 0.05:
    speech.append([cur, dur])
pieces = []                                         # merge speech runs into 2–9 s pieces
for a, b in speech:
    if pieces and (b - pieces[-1][0] <= 9.0 and (a - pieces[-1][1] < 0.6 or pieces[-1][1] - pieces[-1][0] < 2.0)):
        pieces[-1][1] = b
    else:
        pieces.append([a, b])
os.makedirs("cap_pieces", exist_ok=True)
files = []
for i, (a, b) in enumerate(pieces):
    f = f"cap_pieces/p{i:04d}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, a - 0.1):.2f}", "-to", f"{b + 0.1:.2f}", "-i", "cap16k.wav", f],
                   check=True)
    files.append(f)
cmd = ["whisper-cli", "-m", MODEL, "-l", "bn", "-mc", "0", "-bs", "1", "-bo", "1", "-nf", "-t", "8", "-nt", "-oj"]
for f in files:
    cmd += ["-f", f]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def looped(text):
    w = text.split()
    return len(w) >= 4 and max(w.count(x) for x in set(w)) / len(w) > 0.5

out = []
for (a, b), f in zip(pieces, files):
    # whisper writes token bytes; a cut letter is replaced, not fatal
    j = json.loads(open(f + ".json", "rb").read().decode("utf-8", "replace"))
    text = re.sub(r"\s+", " ", " ".join(sg["text"] for sg in j["transcription"])).strip()
    if not text:
        continue
    if looped(text):
        text = "[CHECK: whisper looped here — write what he says] " + text.split()[0]
    # phrases of ≤ 5 words / ~34 characters, timed by their share of the piece's characters
    words, groups, cur = text.split(" "), [], []
    for w in words:
        if cur and (len(cur) >= 5 or len(" ".join(cur + [w])) > 34):
            groups.append(" ".join(cur)); cur = []
        cur.append(w)
    if cur:
        groups.append(" ".join(cur))
    total = sum(len(g) for g in groups) or 1
    t = a
    for g in groups:
        d = (b - a) * len(g) / total
        out.append({"t": round(t, 2), "d": round(d, 2), "text": g})
        t += d
# no gaps that flicker: a caption holds until the next one if they are < 0.4 s apart
for x, y in zip(out, out[1:]):
    if 0 < y["t"] - (x["t"] + x["d"]) < 0.4:
        x["d"] = round(y["t"] - x["t"], 2)
json.dump(out, open("captions_draft.json", "w"), ensure_ascii=False, indent=1)
print(f"captions_draft.json: {len(out)} lines — correct the text, then save as captions.json")
