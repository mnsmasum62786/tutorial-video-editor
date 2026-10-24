# The body edit

Everything lives in `<project>/work`. The edit is an edit-decision list (`edl.json`) built by `$S/edl.py`
from three signals: where it is silent (`silences_safe.txt`), what the screen does (`activity.jsonl`) and your
hints (`hints.json`). Media is rendered from that list, so changing the edit = editing hints and re-running.

## Pauses (never clip a word)
`edl.py` rules, and why:
- Pauses come only from `silences_safe.txt` = true silence (−38 dB, 0.35 s+) ∪ voice-free stretches ≥ 3 s. An
  earlier spectral voice detector treated soft word endings as silence and clipped words; the user noticed.
- Every cut snaps to the quietest 40 ms within 0.6 s of the pause edge; if nothing is ≤ −40 dB the pause is kept.
- ≤ 0.55 s: kept. Still screen: closed to the snap points. Screen busy ≤ 1.2 s: kept. Busy ≤ ~1.4 s more: 2× (muted).
  Longer busy waits (AI working, page loading): fast-forward to ≤ 6 s with a "▶▶ N×" badge (muted).
- `check_cuts.py` must report 0 cut points above −38 dB; `build_all.sh` refuses to render otherwise.

## hints.json
```json
{
  "cut":    [[1.55, 31.8]],          // source seconds removed entirely (retakes, lines the intro used, dead air)
  "face":   [[0, 1.55], [4800, 5040]],// force face (greeting, closing talk)
  "screen": []                        // force screen (he points at something while the cursor is still)
}
```
Cut boundaries must themselves be in silence — check the level there (a cut that ended 0.07 s inside a word once
left a dangling syllable). The body usually opens on his greeting, then jumps past what the intro already used.

## Layout: screen vs face
`edl.py` marks a half-second "face" when nothing on screen changes (not even the cursor) within ±4 s, else
"screen"; face shots ≥ 6 s, screen shots ≥ 3 s. Override with hints where the transcript says otherwise:
"এই যে দেখেন / এখানে" → screen; a long reflective stretch over a static page → face. The browser tabs/bookmarks
bar is cropped off the recording (top 224 px of 1996), which also removes the address bar from privacy concerns.

## Zooms
To the region that changes (union of change boxes over ~5 s), 1.3–1.7×, held ≥ 3 s, only in screen shots at
normal speed. If a zoom keeps landing on a tiny cursor-only change, raise `REAL`/`ACT` thresholds in `edl.py`.

## Chapters
`chapters.json`: `[{"src": 129.0, "n": "CHAPTER 02", "title": "AI Audit", "sub": "৯ মিনিটে পুরো website audit"}]` —
`src` is the source second where the topic starts (put it where the screen shows the new thing, not the first
word about it). `build_all.sh` maps them to output time and writes `YOUTUBE_CHAPTERS.txt`. 8–12 for an hour.
Titles: 1–3 English words; sub: his phrasing in Bengali.

## Explainers (motion graphics on face shots)
After `edl.json` exists, list the face shots (`edl.json` → `shots` with mode "face"), read what he says in each
(transcript times are source times — map them with the segment list), and add explainers where an idea has
shape: a process (flow), a set of things (list), a contrast (compare), a number (stat), a quotable claim
(headline). Format and kinds: `design-guide.md`. Timing: start just after he introduces the idea, items paced
to when he names them, end before he moves on. Skip a face shot that is pure conversation.

## Retakes and inconsistencies — fix what a careful editor would
- **Retakes**: `$S/find_retakes.py` lists sentences said twice within 90 s. Verify each by transcribing
  both pieces; cut the earlier take only when it is a restart (stumble, "না না", "আবার বলি"), not when he
  repeats for emphasis (the "workflow change হয়ে" repetition was emphasis). Add confirmed ones to `hints.cut`.
- **Dead recording**: after the last speech (analyse.sh prints it), and long stretches with no voice and a static
  screen.
- **Speech vs screen mismatch**: he names something that isn't on screen yet → keep screen mode but move the
  chapter/zoom to when it appears; he talks about a screen he already left → force screen for that range only if
  the screen still shows it, otherwise face.
- **Audio**: `voice_chain.py` for every voice file — high-pass, less boom (−2.5 dB @ 220 Hz), presence (+2.5 dB
  @ 3.2 kHz), gentle 2:1 compression, then one static gain to **−14 LUFS** (YouTube's reference) + −1 dBTP limiter.
  Noise reduction only if the room is noisy (background > −55 dBFS): on his setup it softened word endings by up
  to 7 dB, and clear words beat a quieter room.
- **Sync**: camera and screen come from one frame-select pass per source with frame counts verified per chunk —
  if a count is off, stop; never "nudge" audio.
- **Wrong or corrected statements**: if he says something and corrects himself later, keep the correction; if the
  wrong version is a clear slip immediately restated, treat it as a retake. When unsure, list it for the user
  instead of cutting.
Report every content cut you made (source range + reason) in REVIEW.md.

## Prompt cards
For AI-agent videos, list the prompts he sends in `prompts.json` (format: `design-guide.md` → Prompt cards).
Time them to when the prompt is visible and he talks about it, 5–8 s each, in screen shots.

## Notification pop-ups
macOS banners appear top-right — mostly inside the cropped top 224 px, but a tall one (WhatsApp/Slack message
preview) reaches into the picture. Check `sheets/` and the OCR `name`/`email`/`number` hits near the top-right
corner; if a banner with someone's message shows, add an `EXTRA_BOXES` region for those frames (see privacy.md).

## Rendering the body media
`build_all.sh` runs `render_media.py edl.json body cam screen voice`: frame-index `select` in chunks of 80 cuts
(ffmpeg's expression parser fails near 1,000 terms), each chunk seeking to its range, frame count verified, then
joined without re-encoding. Screen output 2560×1326 (sharp under zoom), camera 1920×1080, voice 48 kHz.
