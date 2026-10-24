# Checks, delivery and posting copy

## Before rendering (cheap, catches most problems)
- `check_cuts.py` → 0 cut points above −38 dB.
- `npx hyperframes check` → ok (nested-media and track-density warnings are expected).
- Snapshots: intro (every clip + title), first minute of the body, 3–4 explainers, chapter cards, a fast-forward
  badge, the end card. Look for overlaps with the camera card and text that runs off its column.

## After rendering (always, before saying "ready")
- `ffprobe`: duration = intro + body + outro, 1920×1080, 25 fps.
- Loudness: about **−14 LUFS** integrated (YouTube's reference), true peak ≤ −1 dB, no clipping
  (`ffmpeg -i <file> -af ebur128=peak=true -f null -`).
- No music anywhere: the only audio tracks are his voice and files from `assets/sfx/` (grep the compositions for
  `<audio` and check every `src`).
- Privacy spot checks on the rendered file (`privacy.md` → Verify).
- A few word-cut moments: pick cut points from `edl.json` and listen-proxy them with the level check — the voice
  file was built from the same list, so if `check_cuts.py` passed, the render matches.
- Say what was measured and what was only looked at; nobody listened to the full hour.

## QC checklist (international standard — go through it, write the result in REVIEW.md)
| Area | Check |
|---|---|
| Picture | 1920×1080, 25 fps, no black/frozen frames at joins, camera graded, nothing off-frame or overlapping |
| Sound | −14 LUFS, ≤ −1 dBTP, voice clear and even, no cut words, SFX below the voice, **no music** |
| Story | hook in the first 5 s, intro ≤ 90 s, chapters match content, no dead air, retakes removed |
| Text | spelling (English and Bengali), numbers he said and confirmed, names allowed, captions only in talking-head |
| Privacy | PRIVACY_REPORT.md read, spot checks done (privacy.md → Verify), notification pop-ups checked |
| YouTube | chapters list starts 00:00, end screen 20 s with two frames, thumbnails ready, Shorts if wanted |
Then `review_reel.py` → send him `review_reel.mp4` + `review_reel.txt` with the delivery note.

## When a long job finishes
Renders take hours and he follows from his phone. When `build_all.sh` or a render finishes (or fails), send a
push notification if the session has a notification tool (PushNotification), one line: what finished, length,
and whether checks passed — then the full note in the chat.

## Render
`build_all.sh` renders with `-w auto --crf 18` (~90 min for 70 min of video on an M5; capture ≈ 26 fps, then
encode). The extract cache in `$TMPDIR/hyperframes-extract-cache-*` (12 GB+) holds frames of the footage it
rendered — the script clears it so an older, less-blurred version can't be reused. Status questions: read the
`@hf-progress` lines in `work/render.log` (capture N/total, then encode N/total).

## Delivery note (reply + REVIEW.md)
- Files: the video, `YOUTUBE_CHAPTERS.txt`, `PRIVACY_REPORT.md`, `renders/thumb_*.jpg`, `renders/short_*.mp4`,
  `renders/review_reel.mp4`, and how to set the end-screen elements in YouTube Studio.
- What the video is now (length, structure) and the file.
- What changed since the last version, if any.
- Checks done (privacy spots, cut points, loudness) and what was not checked.
- Things only he can confirm (amounts heard, names kept visible, content cuts made).
- Never hand over a file that failed a privacy check, and say clearly which older files must not be uploaded.

## Posting copy (when asked)
`SOCIAL_POSTS.md` with: YouTube title options (recommend one), description (hook in his words, what's covered,
the lesson, chapters, link placeholders, privacy note, hashtags), tags, pinned comment with a question, thumbnail
text (2–4 words); Facebook page post (short, scannable, link); Facebook group post from his profile (first-person
story, value first, link in the first comment). His voice: Bengali with English tech terms. Facts only from the
video; placeholders for links; flag amounts to confirm; don't name the client unless he does.
