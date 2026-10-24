# Design guide (the user's reference style)

Reference video: `/Users/abdullah/Desktop/Chrome Downloads/WhatsApp Video 2026-10-18 at 5.54.15 PM.mp4`
(126 s, a finished intro he likes). Look at a contact sheet of it before designing anything new. It deliberately
uses glass cards and a blue→purple gradient — HyperFrames lists those as generated-video defaults, but this is the
person's own reference, so it wins.

## Ground
- His own room, heavily blurred and darkened: a still frame of the camera (`assets/room.jpg`) with the
  media-treatment blur, never a CSS filter:
  `npx hyperframes media-treatment --file compositions/intro.html --selector "#in-room" --grading '{"effects":{"blur":0.85},"adjust":{"exposure":-0.55,"saturation":-0.25}}' --apply`
  Copy the resulting `data-color-grading` attribute into `work/room_grading.attr` — `build_body.py` and the end card
  reuse it so every section has the same ground.
- A soft shade over it: `radial-gradient(ellipse at 30% 40%, rgba(70,60,120,.18), rgba(8,8,14,.55) 70%)`.

## Type
- English: **Oswald** 700, uppercase, line-height ~1.02. Headline cards 84–104 px; title card 196 px.
- Bengali: **Kohinoor Bangla** Bold/Semibold via `@font-face { src: local("Kohinoor Bangla Bold"), local("KohinoorBangla-Bold") }`.
  Mixed lines are normal ("Audit থেকে Proposal Sign", "সবকিছু **Agentic AI** দিয়ে").
- Accent: one or two key words per line in `linear-gradient(90deg, #4aa3ff, #8e7dff 55%, #c06cff)` clipped to text.
- Spaced small caps for kickers and sublines (letter-spacing .3–.42em, #b9b9c8).

## Material
- Glass card: `background: rgba(28,28,36,.52–.62); border: 1px solid rgba(255,255,255,.16); border-radius: 22px;
  backdrop-filter: blur(18px); box-shadow: 0 20px 50px rgba(0,0,0,.35)`.
- Pill chips with a coloured dot; numbered steps joined by a gradient line; ✓ chip in green (#2fd27a) for "done/confirmed".
- Camera in a rounded card with a drop shadow; screen windows rounded 18–22 px with a thin light border.

## Layouts (1920×1080)
| Name | Camera | Graphics |
|---|---|---|
| Full face + headline | full frame | glass headline card top-left (70, 70) |
| Side card | whole frame scaled .53, x +391 (right half), round 72 px | left column x 90–820 |
| Screen + mini cam | cam scaled .25 bottom-right | screen window 1600×829 at (60,168), headline above |
| Tutorial screen | cam card 384 px wide bottom-right (28 px margin) | page window 1872 wide at (24,56), browser chrome cropped |
| Title | none | centred kicker / big title / spaced subline |

## Motion vocabulary (keep it simple)
- Text in: blur 10→0 + fade, 0.18 s, `power4.out`. Out: blur + fade 0.16 s `power2.in`. No slide-ups everywhere.
- Chips/pills: `back.out(1.6)` pop, 0.45 s; lists stagger 0.6–0.95 s, timed to when he says each item.
- Camera layout changes: one `fromTo` with explicit both-end states (clip-path `inset()` strings must interpolate
  number-for-number — GSAP reading the browser's shortened string made the window jump once), 0.5–0.6 s `expo.out`/`expo.inOut`.
- Screen zooms: 0.8–0.9 s `power2.inOut`, held ≥ 3 s.
- Punch-in 1.0 ↔ 1.12 on jump cuts in face shots (hides the cut).
- Sound: **no music, ever** — no background music, no jingles, no musical stingers, no tonal risers (he follows
  Islamic guidelines; this overrides HyperFrames' "films over 15 s get a music bed"). Sound effects only, from
  `assets/sfx/`: whoosh on layout changes and transitions, pop on chips/cards, click on real clicks, chime or ping
  for a success moment (test passed, client confirmed), one soft impact under the title. Peaks land one frame after
  the picture; 0.25–0.45 volume, never louder than the voice.

## Sound effects (where, how loud)
| Moment | SFX (assets/sfx) | Volume | Timing |
|---|---|---|---|
| layout change screen ↔ face | whoosh | 0.22 | peak on the fastest frame of the move (`build_body.py` places it) |
| chapter card, prompt card | pop | 0.3–0.35 | as the card lands |
| explainer in | whoosh-short | 0.2 | with the camera move |
| success (test passed, client confirmed) | chime (`"sfx": "chime"` on that explainer) or ping | 0.35 | on the ✓ / result |
| intro title, logo | impact-bass-1 (soft) | 0.3 | on the title |
| a real click he narrates ("এখানে click করবো") | click-soft | 0.25 | at the click |
Fewer is better: never two SFX within 0.5 s, nothing under a sentence's key word. Never music, never a riser.

## Camera look
`media-treatment` preset **clean-studio** on his camera (chosen against none / skin-soft on his room: warmer
skin, cleaner whites, no plastic look). The tested attribute is `assets/cam_grading_clean-studio.attr`;
`build_body.py` and the thumbnails use it unless `work/cam_grading.attr` exists. If a recording's light is very
different (night, new lamp), compare presets on one face frame and save the winner as `work/cam_grading.attr`.

## Name lower-third
Glass card bottom-left with his name (Oswald 54 px, uppercase) and line (28 px, spaced) from `channel.json`,
on the first face shot ≥ 7 s that has no chapter card, for 5 s. Once per video.

## Prompt cards (AI-agent videos)
When he types or pastes a prompt to an agent (Claude, Antigravity, Codex…), the prompt is often the lesson.
`work/prompts.json` `[{"t", "d", "text", "label"}]` (body output seconds) shows it in a dark readable card
bottom-left, monospace, with a label like "Prompt → Antigravity". Take the text from the screen (OCR or the
sheets), shorten with "…" if long, and check it contains no client names/URLs (it's not blurred — it's new text).

## Visual library (what to reach for)
Explainer kinds below; chapter cards; prompt cards; ▶▶ fast-forward badge; ✓ chips for done/confirmed; stat
number; zoom to the region that changes. For something not in this list (a map, a chart, an animated diagram),
look in `/hyperframes-registry` before hand-building, and keep it in this style (glass, gradient accent, blur-in).
Click highlight: the recordings don't log clicks, so zooms (to where the screen changes) do that job; add a
click-soft SFX only where he narrates a click.

## Explainers (face shots in the body)
`work/explainers.json` → `build_body.py` renders them in the side-card layout. Kinds:
- `headline` — one line (+ `sub`). Use for a key claim: `"title": "AI works **like me**"`.
- `list` — chips (`items`), appear in order. Use when he enumerates platforms, tools, options.
- `flow` — numbered steps joined by a line. Use for a process he describes.
- `stat` — one big number (`value`) + title/sub. Only real numbers he said.
- `compare` — `items: [old, new]`, `labels: ["আগে", "এখন"]`. Use for before/after, manual vs AI.
- `big` — one full-frame statement (`title`), camera shrinks to the corner card. The one line of a section
  ("It worked for **9 minutes**"). At most one per few minutes, or it stops landing.
- optional `"sfx": "chime"` on any explainer that shows a success.
Each needs `t`/`d` in body output seconds fully inside a face shot (the script skips any that aren't). 6–12 s each;
pace items to his speech. A few strong ones per chapter beat a graphic on every sentence.
