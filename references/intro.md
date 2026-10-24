# The intro (60–90 s)

The intro's only job: make a stranger want the next hour. It is built from **his own lines** in this recording,
recut into a tighter story, with simple motion graphics in the reference style. The first project's intro (44 s)
is in `assets/intro-example.html` — reuse its CSS, helpers (`move`, `blurIn`, `blurOut`, `popIn`, `zoomTo`) and
layout states; the user now wants 60–90 s, so use 8–12 clips instead of 7.

## 1. Mine the hooks
Read the whole transcript with the screen sheets beside it. Mark candidates of these kinds (best first):
1. **Result / stakes** — money, a confirmed deal, a client outcome ("গতকাল দুটা project confirm — $1,200, $1,000").
2. **The surprising mechanism** — the thing the viewer didn't know was possible ("AI 9 মিনিটে পুরো website audit করলো").
3. **Proof on screen** — a real report, a dashboard, a passing test, at the moment he talks about it.
4. **The problem** — what was broken ("নতুন Join Now flow-তে কোনো purchase event fire হচ্ছিল না").
5. **The belief / lesson** — a quotable line ("AI works like me", "it's like a brain", "Prompt না, skill").
6. **The promise** — what this video will show ("আজকে live করে দেখাবো").
Keep lines that are complete sentences on their own, 2–10 s long. Discard anything that needs context to understand.

**Score each candidate** (write the table in NOTES.md) and build from the top scores:
| Score 0–2 each | 0 | 1 | 2 |
|---|---|---|---|
| Stakes | none | effort/time | money, a client, a result |
| Surprise | expected | interesting | "that's possible?" |
| Proof on screen | none | related screen | the evidence itself |
| Stands alone | needs context | mostly | fully |
| Clear audio | stumble/noise | ok | clean, energetic |
8–10 = open with it; 6–7 = middle; below 5 = leave it. The first 5 seconds must be an 8+.

## 2. Shape the story (pick one order, write it in NOTES.md first)
Stakes → mechanism → proof → lesson → promise → title is the default (it worked). Alternatives: problem → proof →
result → promise; or one striking proof shot first, then stakes. 8–12 clips, 60–90 s of speech, then a 4 s title.
Prefer variety in layout from clip to clip (full face + headline / side card + graphic / screen proof + mini cam).

## 3. Cut clips at quiet points, then verify the words
- Find rough times from the transcript, then the pauses: `silencedetect` on a window around the line.
- Boundaries must sit in silence: snap the start back and the end forward to the nearest 40 ms window ≤ −40 dB
  (search ≤ 0.5 s). A start of −16 dB = a clipped first syllable — this happened and was caught by measuring.
- Transcribe each candidate piece on its own (`whisper-cli -m …large-v3 -l bn -mc 0 -bs 1 -bo 1 -nf -nt piece.wav`)
  and read it: is the sentence complete, does it start/end where you think? Whisper may drop a clip's first phrase.
- Cut: `TVE_SRC=… $S/.venv/bin/python $S/cut_clips.py intro a:b a:b … --screen a:b` → `assets/intro_cam.mp4`,
  `intro_voice.wav` (same voice chain as the body: EQ + gentle compression, −14 LUFS), and the proof screen clip. Then move the screen clip to
  `work/intro_screen_raw.mp4` — `build_all.sh` blurs it into `assets/intro_screen.mp4`.
- If clip timings change later, shift every cue: cues at a cut boundary land exactly on the new boundary, others
  move with their clip, the title shifts by the total change.

## 4. Graphics per clip (simple, from his words)
- Headline card on full face: 2–3 words + one gradient word (WORK / **COMPLETED**, AI WORKS / **LIKE ME**).
- Chips that pop as he says them (amounts, platforms).
- Side card + a mini flow/list (audit report → event mapping → proposal → client signed).
- Proof clip: real screen in a window, zoom to the evidence (e.g. "Worked for 9m"), then to the finding.
- Title: kicker (client · country or topic), big two-word title with gradient first word, spaced subline. If
  `channel.json` has a `logo`, it lands with the title (scale + blur-in, soft impact SFX) — no musical sting.
- Sound: SFX only (whoosh on layout changes, pop on chips, one soft impact on the title). No music bed, no riser —
  his rule; it overrides any "music under intros" default.
Text on screen paraphrases or labels what he says — it never adds a claim he didn't make. Amounts and numbers
heard in Bengali (বারোশো, এক হাজার) go in the delivery note as "please confirm".

## 5. Before moving on
`npx hyperframes check`, then snapshot every clip's middle and every layout change; look for headlines without
`position: absolute` (they render at 0,0), empty glass boxes before their moment, text overlapping the camera card.
