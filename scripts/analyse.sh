#!/bin/bash
# Analyse a 3-file recording. Run inside <project>/work with TVE_SRC set to the recording prefix
# ("/path/My talk_" for "My talk_Camera.mp4", "My talk_Screen.mp4", "My talk_Microphone.mp3").
# Writes: mic16k.wav, silences_dB.txt, silences_vad.txt, silences_safe.txt, activity.jsonl, sheets/
set -euo pipefail
: "${TVE_SRC:?set TVE_SRC to the recording prefix}"
HERE="$(cd "$(dirname "$0")" && pwd)"; PY="$HERE/.venv/bin/python"
mkdir -p sheets
ffmpeg -v error -y -i "${TVE_SRC}Microphone.mp3" -ac 1 -ar 16000 mic16k.wav
# true silence (−38 dB, 0.35 s+): the only places a cut may land
ffmpeg -hide_banner -i mic16k.wav -af silencedetect=noise=-38dB:d=0.35 -f null - 2>&1 \
  | grep -oE "silence_(start|end): [0-9.]+" | awk '{print $1, $2}' > silences_dB.txt
"$PY" "$HERE/vad.py" mic16k.wav silences_vad.txt
"$PY" "$HERE/safe_silences.py"
if [ -f "${TVE_SRC}Screen.mp4" ]; then
  # screen activity every half second (what changes, and where) + thumbnails every 30 s, in parallel
  ( ffmpeg -v error -hwaccel videotoolbox -i "${TVE_SRC}Screen.mp4" -vf "fps=2,scale=640:374,format=gray" -f rawvideo - \
      | "$PY" "$HERE/activity.py" activity.jsonl ) &
  ( ffmpeg -v error -y -hwaccel videotoolbox -i "${TVE_SRC}Screen.mp4" -vf "fps=1/30,scale=480:-1" sheets/s_%04d.jpg ) &
  wait
else
  # talking-head / explainer video: no screen recording. A still "screen" makes edl.py keep him on camera
  # for the whole video; sheets come from the camera so you can still see what he shows (props, gestures).
  echo "no ${TVE_SRC}Screen.mp4 -> talking-head mode (face only, captions, rich explainers)"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TVE_SRC}Camera.mp4")
  "$PY" -c "
import json; d=float('$DUR')
with open('activity.jsonl','w') as f:
    for i in range(int(d*2)+1): f.write(json.dumps({'t': i/2, 'frac': 0.0})+'\n')"
  ffmpeg -v error -y -hwaccel videotoolbox -i "${TVE_SRC}Camera.mp4" -vf "fps=1/15,scale=480:-1" sheets/s_%04d.jpg
fi
n=$(ls sheets/s_*.jpg | wc -l); k=0
while [ $((k * 42)) -lt "$n" ]; do
  ffmpeg -v error -y -start_number $((k * 42 + 1)) -i sheets/s_%04d.jpg -vf "scale=320:-1,tile=7x6" -frames:v 1 sheets/grid_$k.jpg
  k=$((k + 1))
done
"$PY" - <<'PY'
import json
dur = json.loads(open("activity.jsonl").readlines()[-1])["t"]
sil = [l.split() for l in open("silences_dB.txt")]
pairs, s = [], None
for k, v in sil:
    v = float(v)
    if k.startswith("silence_start"): s = v
    elif s is not None: pairs.append((s, v)); s = None
last_speech = max((a for a, b in pairs if b >= dur - 1), default=dur)
print(f"duration {dur/60:.1f} min; speech ends near {last_speech:.1f} s = {last_speech/60:.1f} min (after that: dead recording, cut it)")
PY
echo "sheets: $(ls sheets/grid_*.jpg | tr '\n' ' ')"
