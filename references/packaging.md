# Packaging: end screen, thumbnails, Shorts, review reel, privacy report

All run inside `<project>/work` after `build_all.sh` (they reuse the edited, blurred, loudness-matched media).

## End screen (built by build_all.sh)
`make_outro.py` writes `compositions/outro.html` from `assets/outro-template.html` + `channel.json`: 20 s on the
blurred room — his round photo (`assets/face.jpg`: pick a smiling, eyes-open frame), name, line, SUBSCRIBE pill,
and two empty "WATCH NEXT" frames on the right. YouTube places its end-screen elements over these in Studio:
tell him to add **two video/playlist elements on the two frames** and **the subscribe element on his photo**
(YouTube allows end screens only in the last 5–20 s). Slow ambient motion keeps it from looking frozen. SFX
only (whoosh in, pop on the button).

`channel.json` (work/, else the skill's `assets/channel.json`): `name`, `line`, `cta`, `outro_line`, optional
`logo` (a PNG/SVG he gives — then animate it in the intro title and end screen with a soft impact SFX; a logo
"sting" is never musical).

## Thumbnails
1. `$S/.venv/bin/python $S/make_thumbs.py faces` → `thumbs/face_candidates.jpg`: 24 face frames, each labelled
   with its body second. Pick an expressive one (open eyes; surprise, a smile, pointing) — neutral faces lose clicks.
2. Pick a proof second in `assets/body_screen.mp4` (a report, a passing test, a dashboard). That file is the
   blurred one, so no IDs; still look at the crop.
3. Write `thumbs.json` (format in the script header) with three variants — layouts `face`, `proof`, `split` —
   and 2–5 words each, his claims only (from the hooks; "AI WORKS / LIKE ME", "FULL AUDIT / IN 9 MIN").
4. `$S/.venv/bin/python $S/make_thumbs.py` → `renders/thumb_1..3.jpg` (1280×720) + `thumb_phone_check.jpg` (all at
   320×180, feed size). If a word can't be read at that size, cut words. Suggest which one to use first and that
   he A/B tests them with YouTube's "Test & compare".

## Shorts / Reels
1. Choose 2–4 moments of 15–60 s that make sense with no context: a result, a surprising mechanism, a strong
   opinion, a before/after. Boundaries in pauses (check the level like intro clips — never a cut word).
2. `shorts.json` (body output seconds; format in the script header): `stack` layout (blurred screen on top, face
   below) for screen moments, `face` for talking moments; a 2–5 word title.
3. `python3 $S/make_shorts.py` → `renders/short_N.mp4`, 1080×1920, voice levelled to −14 LUFS, "FULL VIDEO"
   tag at the end. No music. No captions for clips from screen-share tutorials (his rule); for talking-head
   videos, reuse the checked `captions.json` lines that fall in the range (shifted to the short's time).

## Review reel (for his phone)
`$S/.venv/bin/python $S/review_reel.py ../renders/<name>.mp4` → `renders/review_reel.mp4` (1–3 min) +
`review_reel.txt`: intro title, lower-third, every chapter card, explainer and prompt card, the first
fast-forwards, the 8 densest privacy moments (spread ≥ 30 s apart) and the end screen — each clip mapped to its
time in the full video, so "clip 7 looks wrong" is a timestamp. Send it with the delivery note; he can review it
in minutes instead of watching an hour.

## Privacy report
`python3 $S/privacy_report.py` → `PRIVACY_REPORT.md`: what kinds of things were blurred, how many times, distinct
values (masked: first 3 characters + length) and first/last time. It says plainly what OCR cannot cover (things
on camera, things said aloud).
