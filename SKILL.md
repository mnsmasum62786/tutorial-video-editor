---
name: tutorial-video-editor
description: Edit Abdullah's raw recordings (Name_Camera.mp4 + Name_Microphone.mp3, plus Name_Screen.mp4 for screen-share tutorials; Bengali talk with English tech terms) into finished, publish-ready YouTube videos with HyperFrames — hook intro in his reference style, screen share where the screen matters and his face where he explains, motion-graphic explainers, chapters, word-safe pause removal, clean -14 LUFS voice, every client URL/ID/credential/name blurred, 20 s end screen, thumbnails, Shorts and a review reel. Also 5–10 min talking-head explainer videos (no screen file) with checked Bengali captions and rich motion graphics. No music ever (SFX only). Use this whenever he hands over raw tutorial/live-project/screen-record/talking-head files or asks to edit, cut, optimise, "tutorial hisebe edit koro", add an intro, blur client info, make thumbnails or Shorts, or re-render such a video — even if he doesn't name the skill.
---

# Tutorial Video Editor

Turns a long raw recording (typically 30–100 min) into a polished, publish-ready tutorial. The pipeline was
built and corrected on a real project (Agentic Tracking Live Project, 100 min → 69 min) — the rules below
carry the corrections the user made, so follow their reasons, not just their letter.

Read `/hyperframes` first for the composition contract (timing attributes, timelines, media rules); this skill
assumes it. Bundled scripts live in this skill's `scripts/` folder — below, `$S` means that folder (the skill's
base directory, shown when it loads, + `/scripts`). Run `$S/setup.sh` once per machine.

## Where this runs — check first
The full edit needs **his Mac**: the raw files (~11 GB per project) are on it, the privacy OCR uses Apple Vision
(macOS only), decoding uses VideoToolbox, and transcription + rendering take hours. Run `uname` before starting.
- **macOS** (local session, or a session he drives from his phone with **Remote Control**): do everything.
- **Cloud session / claude.ai chat / anything not macOS** (Ubuntu VM: 4 vCPU, 16 GB, 30 GB disk, ~30 min per
  command, no access to his Desktop files): don't attempt the media pipeline. Do the thinking work instead if he
  gives you a transcript, notes or screenshots — hook selection, the intro script, chapter titles, explainer
  texts, `redact_terms.json`, posting copy — and tell him plainly that the render must run on his Mac: open the
  Claude app on the Mac, start (or reuse) a local Code session with Remote Control on, then continue from the phone.

## Two kinds of video — decided by the files
| Files | Mode | What changes |
|---|---|---|
| Camera + Microphone + **Screen** | **screen-share tutorial** (30–100 min) | screen/face layout, zooms, fast-forwards, privacy OCR, **no captions** |
| Camera + Microphone, **no Screen** | **talking-head explainer** (5–10 min) | face all the way, **captions** (checked Bengali), more and more varied explainers, short intro — read `references/talking-head.md` |
The scripts detect the mode themselves (`analyse.sh`, `build_all.sh`, `build_body.py`).

## His fixed rules (never trade these for style)
- **No music, ever** — no background music, intro bed, jingle, musical sting or riser (he follows Islamic
  guidelines). Sound effects are fine: whoosh, pop, click, chime, ping, soft impact — only from `assets/sfx/`.
  This overrides HyperFrames' own "give long films a music bed" default.
- **Captions only in talking-head videos.** Screen-share tutorials never get captions/subtitles.
- **Every word audible** — pauses removed only in true silence.
- **Client privacy** — client URLs, IDs, credentials, contact names and photos blurred everywhere.

## What "done" means

1. **Intro, 60–90 s**, built from the video's own strongest lines, in the reference design (`references/design-guide.md`).
2. **Body**: the whole session in order — screen share while the screen is doing something or he is pointing at it,
   his face full-frame while he explains, motion-graphic explainers over those face moments, zooms to where he
   clicks or types, chapter cards, waits fast-forwarded with a badge.
3. **Every word audible.** Pauses are removed only in true silence. The user caught clipped words once; it is the
   one thing that makes a tighter edit worthless.
4. **Client privacy.** Client URLs/domains, tracking IDs, ad-account numbers, tokens, phone numbers, emails, the
   client contact's name and profile photo — blurred wherever they appear, including while scrolling.
5. **Sound**: his voice cleaned (EQ + gentle compression) at −14 LUFS, SFX under it, no music.
6. **Finish**: camera colour grade, name lower-third once, prompt cards for the prompts he gives AI agents,
   20 s end screen with two "watch next" frames, YouTube chapter list.
7. **Package**: 3 thumbnail options, 2–4 Shorts if he wants them, `PRIVACY_REPORT.md`, a 1–3 min review reel for
   his phone, and (if asked) posting copy for YouTube / Facebook page / group.

## Workflow

Long steps run in the background with `nohup` (sessions can end mid-job; scripts resume). Tell the user what is
running and roughly how long — he will ask for status.

### 1. Set up and analyse (≈15 min for 100 min of footage)
```bash
npx hyperframes init <project>; mkdir -p <project>/work; cd <project>/work
export TVE_SRC="/path/to/Recording name_"          # prefix of the three files
$S/setup.sh
$S/analyse.sh
```
Put his `channel.json` (name, line, CTA — the skill's `assets/channel.json` is the default) in `work/` if it
should differ. `analyse.sh` prints where speech ends — raw recordings often run on with nothing (16 min in the first project);
that tail is cut. Look at `sheets/grid_*.jpg` to learn what is on screen when (apps, client, deliverables).

### 2. Transcribe (≈1× real time of speech)
`$S/transcribe.sh <speech_end_seconds>` → `transcript_src.txt`. Bengali Whisper output is rough; it is
for understanding structure, finding hooks and chapters — never for exact on-screen quotes without checking.
Details and failure modes: `references/transcription.md`.

### 3. Understand the video
Read the transcript and the screen sheets together and write down, in `work/NOTES.md`:
the story (client ask → audit → proposal → build → QA → test → lesson, or whatever this one is), the chapters
(source times), the 6–10 strongest lines (hooks), the stretches where he explains to camera (explainer
candidates), and everything client-identifying you saw (for the privacy terms file). Ask the user only what you
cannot find (e.g. amounts you heard but can't verify).

### 4. Privacy terms — before anything is rendered
Write `work/redact_terms.json` (client domains/slugs + people's names) and read `references/privacy.md` for what
else is blurred automatically and how to verify it. Never render a version you have not privacy-checked: the
first project shipped a render with a client's Google Ads ID half visible during a fast scroll.

### 5. The body edit
```bash
$S/.venv/bin/python $S/edl.py <speech_end> 0      # -> edl.json (segments, shots, zooms, fast-forwards)
$S/.venv/bin/python $S/check_cuts.py               # every cut point must sit in silence
```
`hints.json` steers it (content cuts, forced face/screen ranges). Retakes, contradictions and fixes:
`references/body-edit.md`. Chapters go in `chapters.json` (source times), explainers in `explainers.json`.

### 6. The intro
Mine hooks, cut clips at quiet points, verify each clip's words, then build `compositions/intro.html` from
`assets/intro-example.html`. Full method: `references/intro.md`.

### 7. Build, check, render (≈2 h for a 60–70 min video)
```bash
nohup $S/build_all.sh > build.log 2>&1 &
```
Stages: media → chapters → OCR → blur → composition (body + 20 s end screen) → check → render. Talking-head
mode skips OCR/blur; run `$S/make_captions.py` after the media stage, correct `captions.json`, then let the
composition + render stages run again (`references/talking-head.md`). Then verify the rendered file — the QC
checklist in `references/qa-delivery.md` — before telling him it is ready, and say plainly what was measured vs.
watched. Send a push notification when a long render finishes, if a notification tool is available.

### 8. Package (≈15 min + Shorts render time)
```bash
python3 $S/privacy_report.py                                   # PRIVACY_REPORT.md
$S/.venv/bin/python $S/make_thumbs.py faces                    # pick face_t, write thumbs.json
$S/.venv/bin/python $S/make_thumbs.py                          # renders/thumb_1..3.jpg
python3 $S/make_shorts.py                                      # from shorts.json, if he wants Shorts
$S/.venv/bin/python $S/review_reel.py ../renders/<name>.mp4    # renders/review_reel.mp4 for his phone
```
Details and what to tell him about the YouTube end-screen elements: `references/packaging.md`.

## Principles (why the rules are what they are)

- **Clarity beats tightness.** Cut only where `silencedetect` (−38 dB) finds silence or a 3 s+ voice-free stretch;
  snap each cut to the quietest 40 ms; skip the cut if nothing is quiet. Expect ~70% of raw length, not 60%.
- **Face when he talks to you, screen when the screen talks.** A still screen (not even the cursor moving for
  ±4 s) while he speaks → face. Anything changing → screen. Minimum shot lengths stop flicker.
- **Explain, don't decorate.** Explainers appear only when he is on camera explaining a concept, a list, steps, a
  number or a before/after — built from his own words. If a moment has no clear idea to show, leave his face alone.
- **His words, his claims.** On-screen text, intro lines and social copy use what he said. Never invent numbers,
  durations, results or experience claims (an "8+ years" slipped into a draft once and had to be removed).
- **Privacy first, then beauty.** Over-blurring a few neighbouring words during a scroll is fine; one readable ID
  is not.
- **His look, his sound.** One camera grade, one voice chain, one design language across intro, body, end
  screen, thumbnails and Shorts — that consistency is most of what makes it look professional.
- **Frame-exact media.** Video is selected by frame index and audio by sample, from the same edit list, in
  verified chunks — so 1,000+ cuts cannot drift.

## References
- `references/design-guide.md` — the reference look, layouts, type, motion, SFX table, camera grade, lower-third,
  prompt cards, visual library, explainer kinds
- `references/talking-head.md` — explainer videos without a screen: captions, more graphics, pacing
- `references/packaging.md` — end screen, thumbnails, Shorts, review reel, privacy report
- `references/intro.md` — hook mining and the 60–90 s intro
- `references/body-edit.md` — pauses, layout, zooms, fast-forwards, chapters, explainers, retakes, inconsistencies
- `references/privacy.md` — what to blur, the terms file, known leaks and how they were closed, verification
- `references/transcription.md` — Bengali transcription that doesn't loop or stall
- `references/qa-delivery.md` — QC checklist, loudness, delivery note, notifications, posting copy
- `tests/smoke.sh` — run after changing any script: builds a 3-minute excerpt end to end
