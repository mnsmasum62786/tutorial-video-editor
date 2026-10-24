#!/bin/bash
# Bengali transcript of the whole talk. Run inside <project>/work after analyse.sh.
# Whisper on long Bengali audio loops and stalls on silence, so: feed it speech only (silences
# removed, 0.6 s gaps between runs), no context carry-over (-mc 0), greedy, no temperature fallback.
# Writes transcript_src.json / .txt with times in the original recording.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; PY="$HERE/.venv/bin/python"
END="${1:-}"   # optional: last second of speech (from analyse.sh)
"$PY" "$HERE/make_speech_only.py" ${END:+--end "$END"}
whisper-cli -m "$HOME/.cache/hyperframes/whisper/models/ggml-large-v3.bin" -l bn -mc 0 -bs 1 -bo 1 -nf -t 8 \
  speech_only.wav > tx_speech.log 2>&1
"$PY" "$HERE/merge_tx.py" tx_speech.log
