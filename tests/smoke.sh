#!/bin/bash
# End-to-end smoke test of the pipeline on a 3-minute excerpt. Run after changing any script.
#
#   tests/smoke.sh "/path/Recording name_" [start_seconds] [--talk]
#
# Cuts 180 s from the recording (all three files; --talk leaves out the screen to test talking-head mode) into
# a temp folder, builds a project with a 4 s placeholder intro, runs analyse -> edl -> check_cuts -> build_all,
# then checks the render: duration = intro + body + outro, 1920x1080, -14 LUFS (±1), true peak <= -1 dBTP,
# and no audio source outside the voice files and assets/sfx (no music). Prints PASS/FAIL per check.
set -euo pipefail
SRC="${1:?recording prefix, e.g. \"/Users/me/Desktop/Screen record/My talk_\"}"; START="${2:-600}"; MODE="${3:-}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"; S="$HERE/scripts"; PY="$S/.venv/bin/python"
T="$(mktemp -d "${TMPDIR:-/tmp}/tve-smoke.XXXX")"; echo "workdir $T"
mkdir -p "$T/rec" "$T/proj/work" "$T/proj/compositions" "$T/proj/assets"
ffmpeg -v error -ss "$START" -t 180 -i "${SRC}Camera.mp4" -c copy "$T/rec/Smoke_Camera.mp4"
ffmpeg -v error -ss "$START" -t 180 -i "${SRC}Microphone.mp3" -c copy "$T/rec/Smoke_Microphone.mp3"
[ "$MODE" = "--talk" ] || ffmpeg -v error -ss "$START" -t 180 -i "${SRC}Screen.mp4" -c copy "$T/rec/Smoke_Screen.mp4"
export TVE_SRC="$T/rec/Smoke_"
cd "$T/proj"
ffmpeg -v error -ss 5 -i "$T/rec/Smoke_Camera.mp4" -frames:v 1 -q:v 2 assets/room.jpg
cp assets/room.jpg assets/face.jpg
cat > index.html <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{margin:0;padding:0;box-sizing:border-box}html,body{width:1920px;height:1080px;overflow:hidden;background:#0b0b10}#root{position:relative;width:100%;height:100%}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="30" data-fps="25" data-width="1920" data-height="1080">
<div id="intro" data-composition-id="intro" data-composition-src="compositions/intro.html" data-start="0" data-duration="4" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
<div id="body" data-composition-id="body" data-composition-src="compositions/body.html" data-start="4" data-duration="20" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
<div id="outro" data-composition-id="outro" data-composition-src="compositions/outro.html" data-start="24" data-duration="6" data-track-index="3" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
</div><script>window.__timelines["main"] = gsap.timeline({ paused: true });</script></body></html>
HTML
cat > compositions/intro.html <<'HTML'
<template><style>#root{position:absolute;inset:0;background:#0b0b10;color:#fff;font-family:"Oswald",sans-serif}
#t{position:absolute;left:0;right:0;top:470px;text-align:center;font-size:120px;font-weight:700}</style>
<div id="root" data-composition-id="intro" data-width="1920" data-height="1080"><div id="t">SMOKE TEST</div></div>
<script>const tl=gsap.timeline({paused:true});tl.fromTo("#t",{opacity:0},{opacity:1,duration:0.5},0.2);window.__timelines["intro"]=tl;</script></template>
HTML
cd work
echo '{"client_terms": [], "names": []}' > redact_terms.json
grep -o 'data-color-grading="[^"]*"' "$HERE/assets/intro-example.html" | head -1 | sed 's/^data-color-grading="//; s/"$//' > room_grading.attr
"$S/setup.sh" >/dev/null
"$S/analyse.sh" | tail -2
"$PY" "$S/edl.py" 180 0 | tail -1
"$PY" "$S/check_cuts.py" | tail -1
"$S/build_all.sh" > build.log 2>&1 || { tail -20 build.log; echo "FAIL build"; exit 1; }

R="../renders/proj.mp4"; ok=1
check() { if [ "$2" = 1 ]; then echo "PASS $1"; else echo "FAIL $1"; ok=0; fi; }
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$R")
WANT=$("$PY" -c "import json;print(4+json.load(open('edl.json'))['total']+20)")
check "duration $DUR ~ $WANT" "$("$PY" -c "print(int(abs($DUR-$WANT)<0.2))")"
check "1920x1080" "$([ "$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$R")" = "1920,1080" ] && echo 1 || echo 0)"
LOUD=$(ffmpeg -hide_banner -i "$R" -af ebur128=peak=true -f null - 2>&1)
I=$(echo "$LOUD" | grep -E "^\s+I:" | tail -1 | awk '{print $2}'); P=$(echo "$LOUD" | grep -E "^\s+Peak:" | tail -1 | awk '{print $2}')
check "loudness $I LUFS (target -14)" "$("$PY" -c "print(int(abs($I+14)<=1.0))")"
check "true peak $P dBTP <= -1" "$("$PY" -c "print(int($P<=-0.9))")"
BAD=$(grep -ho '<audio[^>]*src="[^"]*"' ../compositions/*.html | grep -o 'src="[^"]*"' | grep -v -E 'assets/(sfx/|body_voice|intro_voice)' || true)
check "no music (audio only voice + assets/sfx)" "$([ -z "$BAD" ] && echo 1 || echo 0)"
[ -z "$BAD" ] || echo "$BAD"
[ $ok = 1 ] && echo "SMOKE PASS ($T)" || { echo "SMOKE FAIL ($T)"; exit 1; }
