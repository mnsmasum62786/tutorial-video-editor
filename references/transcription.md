# Transcribing his Bengali talks

He speaks Bengali with English tech terms. What works and what failed:

| Approach | Result |
|---|---|
| `npx hyperframes transcribe` default (`small.en`) | translates into garbage English — unusable |
| whisper large-v3 `-l bn` over the full file | loops ("আমার আমার আমার…") after a few minutes |
| 30 s chunks, 3 in parallel | correct but GPU contention made it ~10× slower than real time |
| greedy without `-nf` | stalls on silence, retrying temperatures |
| **speech-only audio + `-mc 0 -bs 1 -bo 1 -nf`, one process** | ≈1× real time of speech, readable |

`$S/transcribe.sh <speech_end>` does the last row: `make_speech_only.py` joins voice runs with 0.6 s gaps and
writes `speech_map.json`; whisper-cli transcribes; `merge_tx.py` maps times back to the recording and drops loop
lines. If a run is interrupted, re-run with `-ot <ms>` from where `tx_speech.log` stopped and pass both logs to
`merge_tx.py`.

Reading it:
- Segment times are good to ~1 s; text is phonetic and often misspelled — read for meaning.
- Unspaced Bengali comes back as long runs; HyperFrames' own transcriber returns one "word" per phrase, so there
  are no word-level times — cut at pauses (`silencedetect`) and verify by transcribing the cut piece.
- English words in his speech ("so AI works like me") come out clean — good anchors for hooks.
- Numbers may come as words (বারোশো = 1,200, এক হাজার = 1,000) — always flag them for the user to confirm.
- Whisper may drop the first phrase of a short clip; that doesn't mean the clip is missing it — check the level.
