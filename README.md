# Tutorial Video Editor (Claude skill)

Turns raw recordings into publish-ready YouTube videos with HyperFrames:

- **Screen-share tutorials** (`Name_Camera.mp4`, `Name_Screen.mp4`, `Name_Microphone.mp3`). Hook intro, screen/face layout, zooms, chapters, explainers, word-safe pause removal and client-privacy blur. No captions.
- **Talking-head explainers** (no screen file). Checked Bengali captions and more varied motion graphics.
- **Always:**
  - no music (sound effects only)
  - voice at −14 LUFS
  - 20 s end screen
  - thumbnails, Shorts and a review reel
  - a privacy report

Start with `SKILL.md`. Run `scripts/setup.sh` once per Mac (Python venv + Apple Vision OCR helper).
After changing scripts, run `tests/smoke.sh "/path/Recording name_"`.

## Install on another machine
```bash
git clone https://github.com/mnsmasum62786/tutorial-video-editor ~/.claude/skills/tutorial-video-editor
~/.claude/skills/tutorial-video-editor/scripts/setup.sh
```
For claude.ai (phone, cloud sessions): zip the folder without `scripts/.venv` and `scripts/bin`, then use Customize → Skills → Add → Upload skill → Upload and replace.
