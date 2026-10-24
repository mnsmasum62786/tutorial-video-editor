#!/bin/bash
# One-time setup: Python venv (numpy, OpenCV) and the OCR binary. Safe to re-run.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$HERE/.venv/bin/python" ]; then
  python3 -m venv "$HERE/.venv"
  "$HERE/.venv/bin/pip" install -q numpy opencv-python-headless
fi
mkdir -p "$HERE/bin"
if [ ! -x "$HERE/bin/ocr_redact" ] || [ "$HERE/ocr_redact.swift" -nt "$HERE/bin/ocr_redact" ]; then
  swiftc -O "$HERE/ocr_redact.swift" -o "$HERE/bin/ocr_redact"
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: brew install ffmpeg"; exit 1; }
command -v whisper-cli >/dev/null || echo "whisper-cli missing (transcription): brew install whisper-cpp"
[ -f "$HOME/.cache/hyperframes/whisper/models/ggml-large-v3.bin" ] || echo "large-v3 model missing: run 'npx hyperframes transcribe <any short wav> -m large-v3 -l bn' once to download it"
echo "ready: $HERE/.venv/bin/python, $HERE/bin/ocr_redact"
