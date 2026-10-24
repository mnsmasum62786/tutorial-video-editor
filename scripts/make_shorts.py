"""Vertical Shorts / Reels (1080x1920) cut from the finished body, from work/shorts.json.

Run inside <project>/work after build_all.sh has made assets/body_*.mp4 (the screen there is already blurred,
the voice already cleaned to -14 LUFS — so a Short inherits the privacy and sound of the main video).

shorts.json:
[
  {"a": 812.0, "b": 858.5,                 # body output seconds; cut at pauses (check_cuts-style: quiet ends)
   "layout": "stack",                      # "stack" = screen on top, face below | "face" = face only
   "focus": 0.35,                          # stack: horizontal centre of the screen crop (0 left … 1 right)
   "kicker": "LIVE CLIENT PROJECT", "l1": "AI DID THE", "accent": "TRACKING AUDIT"}
]
15–60 s each, one complete idea that makes sense without the rest of the video. No music; no captions by
default (his rule for screen-share tutorials) — set "captions": [{"t": 0.0, "d": 2.4, "text": "…"}] only for
a talking-head Short and only with text he has checked.
Output: ../renders/short_1.mp4 …
"""
import html, json, os, subprocess

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAM_GRADING = open("cam_grading.attr").read() if os.path.exists("cam_grading.attr") else \
    open(os.path.join(SKILL, "assets", "cam_grading_clean-studio.attr")).read()
CHANNEL = json.load(open("channel.json" if os.path.exists("channel.json") else os.path.join(SKILL, "assets", "channel.json")))
shorts = json.load(open("shorts.json"))
proj = os.path.abspath("..")
os.makedirs("../renders", exist_ok=True)

def esc(s):
    return html.escape(s)

for n, sh in enumerate(shorts, 1):
    a, b = sh["a"], sh["b"]; D = round(b - a, 2)
    d = f"../shorts/short_{n}"
    os.makedirs(d, exist_ok=True)
    if not os.path.exists(f"{d}/assets"):
        os.symlink(f"{proj}/assets", f"{d}/assets")
    lay = sh.get("layout", "stack")
    fx = sh.get("focus", 0.5)
    caps = "\n".join(
        f'      <div class="clip cap" data-start="{c["t"]}" data-duration="{c["d"]}" data-track-index="{6 + i % 2}">{esc(c["text"])}</div>'
        for i, c in enumerate(sh.get("captions", [])))
    screen = (f'      <div id="sc-win"><video id="sc" class="clip" src="assets/body_screen.mp4" data-start="0" data-duration="{D}" '
              f'data-media-start="{a}" data-track-index="2" muted playsinline></video></div>') if lay == "stack" else ""
    page = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Bangla"; font-weight: 700; src: local("Kohinoor Bangla Bold"), local("KohinoorBangla-Bold"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0b0b10; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Oswald", "Bangla", sans-serif; color: #fff; overflow: hidden; }}
      #cam {{ position: absolute; left: 0; width: 1080px; object-fit: cover; }}
      .lay-stack #cam {{ top: 1100px; height: 820px; object-position: 50% 30%; }}
      .lay-face #cam {{ top: 0; height: 1920px; object-position: 50% 40%; }}
      #sc-win {{ position: absolute; left: 30px; top: 400px; width: 1020px; height: 660px; border-radius: 28px; overflow: hidden;
        border: 2px solid rgba(255,255,255,.22); box-shadow: 0 24px 60px rgba(0,0,0,.5); }}
      #sc {{ width: 100%; height: 100%; object-fit: cover; object-position: {fx * 100:.0f}% 30%; }}
      #shade {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(8,8,14,.92) 0%, rgba(8,8,14,.55) 20%, rgba(8,8,14,0) 34%); }}
      #ttl {{ position: absolute; left: 60px; right: 60px; top: 110px; }}
      .kick {{ display: inline-block; padding: 8px 22px 10px; border-radius: 999px; font-size: 34px; font-weight: 600;
        letter-spacing: .14em; background: rgba(28,28,36,.75); border: 2px solid rgba(160,130,255,.7); }}
      .l1, .acc {{ display: table; font-size: 96px; font-weight: 700; line-height: 1.0; text-transform: uppercase; }}
      .l1 {{ margin-top: 16px; }}
      .acc {{ background: linear-gradient(90deg, #4aa3ff, #8e7dff 55%, #c06cff); -webkit-background-clip: text; background-clip: text; color: transparent; }}
      .cap {{ position: absolute; left: 60px; right: 60px; bottom: 300px; text-align: center; font-size: 64px; font-weight: 700;
        line-height: 1.2; padding: 14px 24px; border-radius: 20px; background: rgba(12,12,20,.78); }}
      #end {{ position: absolute; left: 0; right: 0; bottom: 140px; text-align: center; opacity: 0; }}
      #end span {{ display: inline-block; padding: 16px 40px 18px; border-radius: 999px; font-size: 50px; font-weight: 700;
        background: linear-gradient(90deg, #4aa3ff, #8e7dff 55%, #c06cff); }}
    </style>
  </head>
  <body>
    <div id="root" class="lay-{lay}" data-composition-id="main" data-start="0" data-duration="{D}" data-fps="25" data-width="1080" data-height="1920">
      <video id="cam" class="clip" src="assets/body_cam.mp4" data-color-grading="{CAM_GRADING}" data-start="0" data-duration="{D}"
        data-media-start="{a}" data-track-index="1" muted playsinline></video>
{screen}
      <div id="shade"></div>
      <div id="ttl"><div class="kick">{esc(sh.get("kicker", ""))}</div><div class="l1">{esc(sh.get("l1", ""))}</div><div class="acc">{esc(sh.get("accent", ""))}</div></div>
{caps}
      <div id="end"><span>FULL VIDEO · {esc(CHANNEL["name"].upper())}</span></div>
      <audio id="vo" class="clip" src="assets/body_voice.wav" data-start="0" data-duration="{D}" data-media-start="{a}" data-track-index="3"></audio>
      <audio id="sw" class="clip" src="assets/sfx/whoosh-short.mp3" data-start="0" data-duration="0.6" data-track-index="4" data-volume="0.25"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#ttl > *", {{ opacity: 0, y: 24, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out", stagger: 0.12 }}, 0.05);
      tl.fromTo("#sc-win", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "expo.out" }}, 0.1);
      gsap.utils.toArray(".cap").forEach((el) => {{
        const t = parseFloat(el.dataset.start);
        tl.fromTo(el, {{ opacity: 0, scale: 0.92 }}, {{ opacity: 1, scale: 1, duration: 0.18, ease: "back.out(1.6)" }}, t);
      }});
      tl.fromTo("#end", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }}, {max(0.5, D - 2.5)});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
    open(f"{d}/index.html", "w").write(page)
    out = os.path.abspath(f"../renders/short_{n}.mp4")
    r = subprocess.run(["npx", "hyperframes", "render", "-w", "auto", "--crf", "18", "-o", out, "."], cwd=d,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"short_{n}: FAILED\n" + r.stderr[-800:]); continue
    # a short slice of the body can sit a few dB off the whole video's -14 LUFS: level it, video untouched
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float([l for l in err.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    tmp = out + ".lvl.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af",
                    f"volume={-14 - I:.2f}dB,alimiter=limit=0.89:level=false", "-c:a", "aac", "-b:a", "192k", tmp], check=True)
    os.replace(tmp, out)
    print(f"short_{n}: {D}s {lay}, voice {I:.1f} -> -14 LUFS -> renders/short_{n}.mp4")
