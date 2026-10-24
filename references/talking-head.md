# Talking-head / explainer videos (5–10 min, no screen recording)

Detected automatically: the recording has `Name_Camera.mp4` + `Name_Microphone.mp3` and **no** `Name_Screen.mp4`.
(If he recorded on camera only, extract the mic once: `ffmpeg -i "Name_Camera.mp4" -vn -ac 1 -ar 48000
"Name_Microphone.mp3"` next to the camera file.) `analyse.sh` writes a still "screen", so `edl.py` keeps him on
camera all the way; `build_all.sh` skips screen OCR/blur and renders camera + voice only.

The difference from a tutorial: nothing on screen carries the viewer, so **the edit has to explain** — captions,
and a motion graphic for every idea that has a shape.

## Captions (only here — never in screen-share tutorials, his rule)
1. After `build_all.sh` has made the media (`assets/body_voice.wav`), run `$S/make_captions.py` →
   `captions_draft.json`. It cuts the voice at its pauses into 2–9 s pieces and transcribes each one separately:
   on a whole track Whisper looped "এই এই এই…" for a minute; per piece a loop stays in one piece and is flagged
   `[CHECK: …]`.
2. **Rewrite the draft** into `captions.json` — Whisper's Bengali is phonetic ("঵েভিসাইড়ের", "কোপি করছে"):
   - correct Bengali spelling; English tech words in English (GA4, GTM, Claude Code, Playwright MCP, page, join);
   - keep times; merge/split lines so each is one phrase, ≤ ~34 characters, readable in ~1.5 s;
   - fillers and false starts ("so", "না না", a doubled word) out; meaning unchanged — never add words he didn't say;
   - one `**accent**` every few lines on the word that matters (a number, a result, a tool name);
   - a `[CHECK]` line or a phrase you can't make out: drop it (no caption) rather than guess, and list those
     times for him.
3. Show him the caption list (or the review reel) before the final render. Wrong words on screen are worse than none.

Look: bottom-centre, white Oswald / Kohinoor Bangla Bold, dark rounded backing, quick 0.14 s rise — no bouncing
words, no karaoke colour sweep (they read as entertainment, and Bengali shaping breaks with per-letter effects).
While a side-card explainer is up, captions move under its left column; during a full-frame `big` statement they
stay clear of the corner camera. The name lower-third and prompt cards sit above the caption line.

## Motion graphics — more of them, more kinds
In a tutorial the screen is the visual; here explainers are. Aim for one every 30–60 s, each from his words
(`explainers.json`, kinds in `design-guide.md`):
| He is… | Use |
|---|---|
| naming 2–5 things (tools, platforms, problems) | `list` — chips timed to each name |
| describing a process | `flow` — numbered steps |
| contrasting old/new, manual/AI, wrong/right | `compare` |
| saying a number or result | `stat` (only numbers he said) |
| landing the one line of the video | `big` — full-frame statement, camera to the corner card |
| introducing a term | `headline` + `sub` definition |
Vary the kinds; never two of the same kind back to back. Between topics, a chapter card (`chapters.json`, `src`
in recording seconds) gives a clear section break with a whoosh. Jump cuts already alternate 1.0 ↔ 1.1 punch-ins.

## Pace and length
5–10 min target. Pauses are cut by the same rules as tutorials (never clip a word). Content: cut restarts and
repeated explanations (`find_retakes.py`), keep the strongest version. The hook intro is shorter here: 20–40 s
(3–5 of his best lines + title), because the whole video is short.

## Privacy
No screen OCR here, so look at the camera sheets (`sheets/grid_*.jpg`) yourself: papers, a phone screen, a
monitor behind him, a whiteboard. If something client-related is readable, blur that region of the camera
with a separate masked asset (ask him first — it's rare).
