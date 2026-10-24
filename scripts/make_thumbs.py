"""Thumbnails: three 1280x720 options in the reference style, from work/thumbs.json.

Run inside <project>/work after the body media exists (assets/body_cam.mp4, assets/body_screen.mp4 — the
screen file is the already-blurred one, so proof shots carry no client IDs).

thumbs.json:
{
  "face_t": 812.4,                 # body output second with a clear, eyes-open, expressive face
  "proof_t": 1530.2,               # body output second with the proof on screen (report, passing test, dashboard)
  "proof_crop": [0.05, 0.1, 0.6, 0.6],   # optional x, y, w, h (fractions) of the screen frame to show
  "variants": [
    {"layout": "face",  "kicker": "LIVE CLIENT PROJECT", "l1": "AI DID THE", "accent": "TRACKING AUDIT"},
    {"layout": "proof", "kicker": "9 MIN AUDIT",         "l1": "AI WORKS",   "accent": "LIKE ME"},
    {"layout": "split", "kicker": "BEFORE → AFTER",      "l1": "NO MORE",    "accent": "MANUAL AUDITS"}
  ]
}
Text: 2–5 words in total, his claims only. Output: ../renders/thumb_1.jpg … and thumb_phone_check.jpg (all
options at phone-feed size, 320x180 — if a word can't be read there, shorten it).
"""
import html, json, os, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = "../thumbs"
os.makedirs(f"{T}/assets", exist_ok=True)

if sys.argv[1:] == ["faces"]:
    # `make_thumbs.py faces` -> thumbs/face_candidates.jpg: 24 face-shot frames labelled with their body second.
    # Pick one with open eyes and a clear expression (a smile, surprise, pointing) for face_t.
    edl = json.load(open("edl.json")); sh = edl["shots"]
    spans = [(s["t"], (sh[i + 1]["t"] if i + 1 < len(sh) else edl["total"])) for i, s in enumerate(sh) if s["mode"] == "face"]
    total = sum(b - a for a, b in spans) or 1
    ts = []
    for k in range(24):
        x = (k + 0.5) * total / 24
        for a, b in spans:
            if x <= b - a:
                ts.append(round(a + x, 1)); break
            x -= b - a
    import cv2, numpy as np                       # the skill's .venv has OpenCV; ffmpeg here has no drawtext
    cap = cv2.VideoCapture("../assets/body_cam.mp4"); tiles = []
    for t in ts:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        fr = cv2.resize(fr if ok else np.zeros((1080, 1920, 3), np.uint8), (480, 270))
        cv2.rectangle(fr, (0, 0), (130, 44), (0, 0, 0), -1)
        cv2.putText(fr, f"{t}", (8, 33), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        tiles.append(fr)
    rows = [np.hstack(tiles[r * 6:(r + 1) * 6]) for r in range(4)]
    cv2.imwrite(f"{T}/face_candidates.jpg", np.vstack(rows))
    print("thumbs/face_candidates.jpg — the number on each frame is its face_t"); sys.exit()

cfg = json.load(open("thumbs.json"))
CAM_GRADING = open("cam_grading.attr").read() if os.path.exists("cam_grading.attr") else \
    open(os.path.join(SKILL, "assets", "cam_grading_clean-studio.attr")).read()

os.makedirs("../renders", exist_ok=True)

def grab(src, t, out, vf=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-q:v", "2"]
    if vf:
        cmd += ["-vf", vf]
    subprocess.run(cmd + [out], check=True)

crop = cfg.get("proof_crop")
proof_vf = f"crop=iw*{crop[2]}:ih*{crop[3]}:iw*{crop[0]}:ih*{crop[1]}" if crop else None
faces, proofs = {}, {}
for i, v in enumerate(cfg["variants"]):
    ft, pt = v.get("face_t", cfg["face_t"]), v.get("proof_t", cfg.get("proof_t"))
    if ft not in faces:
        faces[ft] = f"assets/face_{len(faces)}.jpg"; grab("../assets/body_cam.mp4", ft, f"{T}/{faces[ft]}")
    if pt is not None and pt not in proofs:
        proofs[pt] = f"assets/proof_{len(proofs)}.jpg"; grab("../assets/body_screen.mp4", pt, f"{T}/{proofs[pt]}", proof_vf)

def esc(s):
    return html.escape(s)

scenes = []
for i, v in enumerate(cfg["variants"]):
    face = faces[v.get("face_t", cfg["face_t"])]
    proof = proofs.get(v.get("proof_t", cfg.get("proof_t")))
    lay = v.get("layout", "face")
    text = (f'<div class="kick">{esc(v.get("kicker", ""))}</div>'
            f'<div class="l1">{esc(v.get("l1", ""))}</div><div class="acc">{esc(v.get("accent", ""))}</div>')
    face_img = f'<img class="face" src="{face}" data-color-grading="{CAM_GRADING}" alt="" />'
    proof_img = f'<div class="proof"><img src="{proof}" alt="" /></div>' if proof else ""
    scenes.append(f'''    <div id="th{i}" class="clip scene lay-{lay}" data-start="{i}" data-duration="1" data-track-index="{i + 1}">
      {face_img}<div class="fade"></div>{proof_img if lay != "face" else ""}<div class="txt">{text}</div>
    </div>''')

page = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Bangla"; font-weight: 700; src: local("Kohinoor Bangla Bold"), local("KohinoorBangla-Bold"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #0b0b10; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Oswald", "Bangla", sans-serif; color: #fff; }}
      .scene {{ position: absolute; inset: 0; overflow: hidden; background: #0b0b10; }}
      .face {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }}
      .lay-face .face {{ transform: scale(1.15) translateX(9%); transform-origin: 50% 35%; }}
      .lay-proof .face, .lay-split .face {{ left: 820px; width: 1100px; object-position: 50% 30%; }}
      .fade {{ position: absolute; inset: 0;
        background: linear-gradient(90deg, rgba(8,8,14,.96) 0%, rgba(8,8,14,.85) 38%, rgba(8,8,14,.15) 70%, rgba(8,8,14,0) 100%); }}
      .txt {{ position: absolute; left: 80px; top: 110px; width: 1100px; }}
      .kick {{ display: inline-block; padding: 10px 26px 12px; border-radius: 999px; font-size: 44px; font-weight: 600;
        letter-spacing: .14em; background: rgba(28,28,36,.75); border: 2px solid rgba(160,130,255,.7); }}
      .l1, .acc {{ display: table; font-size: 170px; font-weight: 700; line-height: .98; text-transform: uppercase; }}
      .l1 {{ margin-top: 26px; text-shadow: 0 8px 30px rgba(0,0,0,.6); }}
      .acc {{ background: linear-gradient(90deg, #4aa3ff, #8e7dff 55%, #c06cff); -webkit-background-clip: text;
        background-clip: text; color: transparent; filter: drop-shadow(0 8px 24px rgba(0,0,0,.55)); }}
      .lay-proof .l1, .lay-proof .acc {{ font-size: 140px; }}
      .proof {{ position: absolute; overflow: hidden; border-radius: 26px; border: 3px solid rgba(255,255,255,.75);
        box-shadow: 0 30px 70px rgba(0,0,0,.6); }}
      .proof img {{ width: 100%; height: 100%; object-fit: cover; }}
      .lay-proof .proof {{ left: 90px; top: 590px; width: 820px; height: 430px; transform: rotate(-3deg); }}
      /* split: the proof is the hero on the left, his face on the right, the words on a band across the bottom */
      .lay-split .fade {{ background: linear-gradient(0deg, rgba(8,8,14,.95) 0%, rgba(8,8,14,.7) 34%, rgba(8,8,14,0) 60%); }}
      .lay-split .proof {{ left: 40px; top: 40px; width: 1000px; height: 640px; transform: rotate(-2deg); }}
      .lay-split .txt {{ top: auto; bottom: 60px; }}
      .lay-split .kick {{ display: none; }}
      .lay-split .l1, .lay-split .acc {{ display: inline-block; font-size: 150px; margin-right: 34px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{len(scenes)}" data-fps="25" data-width="1920" data-height="1080">
{chr(10).join(scenes)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
'''
open(f"{T}/index.html", "w").write(page)
at = ",".join(f"{i + 0.5}" for i in range(len(scenes)))
out = os.path.abspath(f"{T}/snaps")
subprocess.run(["npx", "hyperframes", "snapshot", "--at", at, "--no-end", "--describe", "false", "-o", out, "."],
               cwd=T, check=True, stdout=subprocess.DEVNULL)
shots = sorted(f for f in os.listdir(out) if f.startswith("frame-") and f.endswith(".png"))
for i, f in enumerate(shots, 1):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/{f}", "-vf", "scale=1280:720", "-q:v", "2",
                    f"../renders/thumb_{i}.jpg"], check=True)
# what a viewer sees in the feed: all options side by side at 320x180
ins = sum((["-i", f"../renders/thumb_{i}.jpg"] for i in range(1, len(shots) + 1)), [])
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                "".join(f"[{i}]scale=320:180[s{i}];" for i in range(len(shots))) +
                "".join(f"[s{i}]" for i in range(len(shots))) + f"hstack=inputs={len(shots)}",
                "../renders/thumb_phone_check.jpg"] if len(shots) > 1 else
               ["ffmpeg", "-v", "error", "-y", *ins, "-vf", "scale=320:180", "../renders/thumb_phone_check.jpg"], check=True)
print(f"{len(shots)} thumbnails -> renders/thumb_*.jpg (+ thumb_phone_check.jpg)")
