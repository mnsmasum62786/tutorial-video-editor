#!/bin/bash
# Build everything after the edit list (edl.json), intro and chapters are ready.
# Run inside <project>/work with TVE_SRC set. Stops on the first failure; re-running skips
# finished stages (delete a stage's output to redo it). Uses nohup-friendly plain output.
#
#   stages: media -> chapters -> ocr -> blur -> composition -> check -> render
set -euo pipefail
: "${TVE_SRC:?set TVE_SRC to the recording prefix}"
HERE="$(cd "$(dirname "$0")" && pwd)"; PY="$HERE/.venv/bin/python"; OCR="$HERE/bin/ocr_redact"
TERMS=redact_terms.json
[ -f "$TERMS" ] || [ ! -f "${TVE_SRC}Screen.mp4" ] || { echo "write work/$TERMS first (client_terms, names)"; exit 1; }
OUTRO=${OUTRO:-20.0}                              # YouTube end screens need 5–20 s; 20 gives room for two videos
INTRO=$("$PY" -c "import re;print(re.search(r'id=\"intro\"[^>]*data-duration=\"([\d.]+)\"',open('../index.html').read()).group(1))")
echo "intro ${INTRO}s, outro ${OUTRO}s"

TALK=0; [ -f "${TVE_SRC}Screen.mp4" ] || { TALK=1; echo "talking-head mode: no screen recording"; }

echo "== media"
if [ ! -f ../assets/body_cam.mp4 ] || [ edl.json -nt ../assets/body_cam.mp4 ]; then
  rm -rf chunks
  "$PY" "$HERE/check_cuts.py"                       # refuse to render cuts that land on speech
  if [ $TALK = 1 ]; then
    "$PY" "$HERE/render_media.py" edl.json body cam voice
  else
    "$PY" "$HERE/render_media.py" edl.json body cam screen voice
    mv body_screen.mp4 body_screen_raw.mp4
  fi
  mv body_cam.mp4 ../assets/body_cam.mp4; mv body_voice.wav ../assets/body_voice.wav
fi

echo "== chapters"
"$PY" - <<'PY'
import json, os
if os.path.exists("chapters.json"):
    e = json.load(open("edl.json")); FPS = 25
    def out_t(src):
        f = src * FPS
        for s in e["segs"]:
            if s["a"] <= f < s["b"]: return (s["t"] + (f - s["a"]) / s["k"]) / FPS
            if s["a"] >= f: return s["t"] / FPS
    ch = json.load(open("chapters.json"))
    for c in ch: c["t"] = round(out_t(c["src"]), 2)
    json.dump(ch, open("chapters.json", "w"), ensure_ascii=False, indent=1)
    print([(c["title"], c["t"]) for c in ch])
PY

if [ $TALK = 0 ]; then
echo "== ocr"
if [ ! -s ocr/body.jsonl ] || [ body_screen_raw.mp4 -nt ocr/body.jsonl ] || [ $TERMS -nt ocr/body.jsonl ]; then
  rm -rf ocr/body && mkdir -p ocr/body
  ffmpeg -v error -y -hwaccel videotoolbox -i body_screen_raw.mp4 -vf "select='not(mod(n\,5))'" -fps_mode passthrough -q:v 2 -start_number 0 ocr/body/%06d.jpg
  find "$PWD/ocr/body" -name "*.jpg" | sort > ocr/body_all.txt      # find, not ls: too many files for a glob
  "$PY" -c "
L=open('ocr/body_all.txt').read().splitlines()            # split on newlines: paths contain spaces
for i in range(3): open(f'ocr/body_part_{i}.txt','w').write('\n'.join(L[i::3])+'\n')"
  for i in 0 1 2; do "$OCR" ocr/body_part_$i.txt $TERMS > ocr/body_part_$i.jsonl & done
  wait
  cat ocr/body_part_0.jsonl ocr/body_part_1.jsonl ocr/body_part_2.jsonl | grep -v '^$' > ocr/body.jsonl
fi
# the intro's screen clip is checked on its own: it changes whenever the intro is re-cut
if [ -f intro_screen_raw.mp4 ] && { [ ! -s ocr/intro.jsonl ] || [ intro_screen_raw.mp4 -nt ocr/intro.jsonl ] || [ $TERMS -nt ocr/intro.jsonl ]; }; then
  rm -rf ocr/intro && mkdir -p ocr/intro
  ffmpeg -v error -y -i intro_screen_raw.mp4 -q:v 2 -start_number 0 ocr/intro/%06d.jpg
  find "$PWD/ocr/intro" -name "*.jpg" | sort > ocr/intro_list.txt
  "$OCR" ocr/intro_list.txt $TERMS > ocr/intro.jsonl
fi
echo "body samples: $(wc -l < ocr/body.jsonl) (expected $(( ($(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 body_screen_raw.mp4) + 4) / 5 )))"

echo "== blur"
if [ -f intro_screen_raw.mp4 ]; then
  EXTRA=""; [ -f intro_extra.json ] && EXTRA=intro_extra.json
  EXTRA_BOXES=$EXTRA "$PY" "$HERE/redact_bake.py" intro_screen_raw.mp4 ocr/intro.jsonl 1 ../assets/intro_screen.mp4 3
fi
"$PY" "$HERE/redact_bake.py" body_screen_raw.mp4 ocr/body.jsonl 5 ../assets/body_screen.mp4 7
fi   # talking-head mode has no screen to read — but still look at the camera sheets for papers, phones, monitors

echo "== composition"
mkdir -p ../assets/sfx && cp "$HERE"/../assets/sfx/*.mp3 ../assets/sfx/     # sound effects only — never music
"$PY" "$HERE/build_body.py"
"$PY" "$HERE/make_outro.py"
"$PY" - <<PY
import json, re
T = json.load(open("edl.json"))["total"]; I = float("$INTRO"); E = float("$OUTRO")
p = "../index.html"; s = open(p).read()
s = re.sub(r'(id="root" data-composition-id="main" data-start="0" data-duration=")[\d.]+', lambda m: m.group(1) + f"{I+T+E:.2f}", s)
s = re.sub(r'(id="body" [^>]*?data-start=")[\d.]+(" data-duration=")[\d.]+', lambda m: m.group(1) + f"{I}" + m.group(2) + f"{T}", s)
s = re.sub(r'(id="outro" [^>]*?data-start=")[\d.]+(" data-duration=")[\d.]+', lambda m: m.group(1) + f"{I+T:.2f}" + m.group(2) + f"{E}", s)
open(p, "w").write(s)
try:
    ch = json.load(open("chapters.json"))
    def ts(t):
        t = int(t); h, m, sec = t // 3600, (t % 3600) // 60, t % 60
        return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
    lines = ["00:00 Intro"] + [f"{ts(c['t'] + I)} {c['title']} — {c['sub']}" for c in ch]
    open("../YOUTUBE_CHAPTERS.txt", "w").write("\n".join(lines) + "\n")
except FileNotFoundError:
    pass
print(f"total {I+T+E:.2f}s (intro {I}, body {T}, outro {E})")
PY

echo "== check"
cd ..
rm -rf "${TMPDIR:-/tmp}/hyperframes-extract-cache-$(id -u)"     # frames of older footage
npx hyperframes check --json 2>/dev/null > work/check.json || true
node -e 'const s=require("fs").readFileSync("work/check.json","utf8");const j=JSON.parse(s.slice(s.indexOf("{\n")));console.log("check ok",j.ok);if(!j.ok)process.exit(1)'

echo "== render"
NAME=$(basename "$PWD")
npx hyperframes render -w auto --crf 18 -o "renders/$NAME.mp4" > work/render.log 2>&1
tail -3 work/render.log
echo "== done: renders/$NAME.mp4"
