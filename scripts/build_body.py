"""Write compositions/body.html from edl.json (+ chapters.json, explainers.json if present).

Run from the project's work/ folder (it writes ../compositions/body.html).

Layout per shot: "screen" = the page in a large rounded window over the blurred room with the
camera in a card bottom-right; "face" = the camera full frame. Zooms follow the activity map.
Jump cuts inside a face shot alternate a 1.0 / 1.1 punch-in so they read as intended.

explainers.json — motion graphics while he talks to camera (only inside face shots):
  [{"t": 812.4, "d": 9, "kind": "flow", "title": "Tracking-এর **৩ ধাপ**",
    "items": ["Audit", "Event Mapping", "Implement"], "sub": "optional line"}]
  kind: headline | list | flow | stat (uses "value") | compare (items = [old, new], "labels" optional)
  t/d are output seconds of the body. **word** gets the accent gradient. During an explainer the
  camera moves into a card on the right and the graphic builds on the left (reference style).
"""
import json, os, re, html as _html

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRADING = open("room_grading.attr").read()  # same blurred-room treatment as the intro (media-treatment output)
# camera look: the project's own grade if made, else the tested default (media-treatment preset "clean-studio")
CAM_GRADING = open("cam_grading.attr").read() if os.path.exists("cam_grading.attr") else \
    open(os.path.join(SKILL, "assets", "cam_grading_clean-studio.attr")).read()
CHANNEL = json.load(open("channel.json" if os.path.exists("channel.json") else os.path.join(SKILL, "assets", "channel.json")))

edl = json.load(open("edl.json"))
FPS = edl["fps"]
TOTAL = edl["total"]
shots, zooms, ffwd, segs = edl["shots"], edl["zooms"], edl["ffwd"], edl["segs"]
chapters = json.load(open("chapters.json")) if os.path.exists("chapters.json") else []
explainers = json.load(open("explainers.json")) if os.path.exists("explainers.json") else []
# prompts.json: the prompt he types to an AI agent, shown as a readable card over the screen
#   [{"t": 312.0, "d": 6, "text": "Can you check the GA4 integration…", "label": "Prompt → Antigravity"}]
prompts = json.load(open("prompts.json")) if os.path.exists("prompts.json") else []
# talking-head mode: no screen recording -> no screen window, captions allowed
TALK = not os.path.exists("../assets/body_screen.mp4")
# captions.json (talking-head videos only — his rule: screen-share tutorials never get captions):
#   [{"t": 3.2, "d": 2.4, "text": "AI এখন **আমার মতো** কাজ করে"}]   output seconds, text he has checked
captions = json.load(open("captions.json")) if os.path.exists("captions.json") else []
if captions and not TALK:
    print("captions.json ignored: this is a screen-share tutorial (no captions there — his rule)")
    captions = []

# screen window geometry (content area 2560x1326 of the recording)
WX, WY, WW = 24, 56, 1872
WH = round(WW * 1326 / 2560)
# camera card in screen mode (whole camera frame scaled into it)
CW = 384
CS = CW / 1920
CX = 1920 - 28 - CW / 2
CY = 1080 - 28 - CW * 9 / 16 / 2

def r(v, n=3):
    return round(v, n)

shot_list = []
for i, s in enumerate(shots):
    end = shots[i + 1]["t"] if i + 1 < len(shots) else TOTAL
    shot_list.append([r(s["t"]), r(end), s["mode"]])

# cut points inside face shots (for alternating punch-ins)
cuts = [r(sg["t"] / FPS) for sg in segs[1:]]
face_cuts = []
for a, b, m in shot_list:
    if m != "face":
        continue
    flip = 0
    for c in cuts:
        if a < c < b:
            flip ^= 1
            face_cuts.append([c, 1.1 if flip else 1.0])

zoom_list = [[r(z["t"]), z["s"], z["x"], z["y"]] for z in zooms]

def rich(text):
    """escape, then **word** -> accent gradient; Bengali runs get the Bangla face"""
    t = _html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r'<span class="grad">\1</span>', t)
    return re.sub(r"([\u0980-\u09FF][\u0980-\u09FF\s,।?!]*)", r'<span class="bn">\1</span>', t)

exp_ok = []
for e in explainers:
    inside = any(a <= e["t"] - 0.4 and e["t"] + e["d"] + 0.4 <= b and m == "face" for a, b, m in shot_list)
    if not inside:
        print(f"skip explainer at {e['t']}s: not fully inside a face shot")
        continue
    exp_ok.append(e)

def exp_body(e):
    k = e.get("kind", "headline")
    head = f'<div class="ex-title">{rich(e["title"])}</div>' if e.get("title") else ""
    sub = f'<div class="ex-sub">{rich(e["sub"])}</div>' if e.get("sub") else ""
    items = e.get("items", [])
    if k == "list":
        inner = "".join(f'<div class="glass ex-chip"><i></i>{rich(x)}</div>' for x in items)
        return head + f'<div class="ex-list">{inner}</div>' + sub
    if k == "flow":
        inner = "".join(f'<div class="glass ex-step"><b>{i + 1:02d}</b>{rich(x)}</div>' for i, x in enumerate(items))
        return head + f'<div class="ex-flow"><div class="ex-line"></div>{inner}</div>' + sub
    if k == "stat":
        return head + f'<div class="ex-stat grad">{rich(e.get("value", ""))}</div>' + sub
    if k == "big":       # full-frame statement, camera shrinks to the corner card
        return f'<div class="ex-big-t">{rich(e["title"])}</div>' + sub
    if k == "compare":
        labels = e.get("labels", ["আগে", "এখন"])
        cols = "".join(f'<div class="glass ex-col"><div class="ex-col-l">{rich(l)}</div><div>{rich(x)}</div></div>'
                       for l, x in zip(labels, items[:2]))
        return head + f'<div class="ex-compare">{cols}</div>' + sub
    return head + sub

# name lower-third: the first face shot long enough to read it
# (never while a chapter card is up: both live bottom-left)
def _free(t, d=5.0):
    return all(t + d <= c["t"] - 0.3 or t >= c["t"] + 4.5 for c in chapters)
lt_t = None
for a, b, m in shot_list:
    if m != "face" or b - a < 7:
        continue
    for t in (a + 0.8, a + 5.2, a + 9.6):
        if t + 5 <= b - 0.5 and _free(t):
            lt_t = r(t); break
    if lt_t is not None:
        break
lt_html = (f'    <div id="bd-lt" class="clip lt" data-start="{lt_t}" data-duration="5" data-track-index="7">'
           f'<div class="glass lt-card"><div class="lt-name">{_html.escape(CHANNEL["name"])}</div>'
           f'<div class="lt-line">{_html.escape(CHANNEL.get("line", ""))}</div></div></div>') if lt_t is not None else ""

prompt_html = "\n".join(
    f'    <div id="bd-pr{i}" class="clip pr" data-start="{p["t"]}" data-duration="{p["d"]}" data-track-index="8">'
    f'<div class="glass pr-card"><div class="pr-label">{_html.escape(p.get("label", "Prompt"))}</div>'
    f'<div class="pr-text">{_html.escape(p["text"])}</div></div></div>'
    for i, p in enumerate(prompts))

# sound effects only — never music (his rule): whoosh on layout changes, pop on cards, chime on success
sfx = []
for i, (a, b, m) in enumerate(shot_list[1:], 1):
    if m != shot_list[i - 1][2]:
        sfx.append(("whoosh.mp3", a - 0.3 + 0.22 - 0.16, 0.22))       # peak at the fastest frame of the move
for c in chapters:
    sfx.append(("pop.mp3", c["t"] + 0.1 + 0.03 - 0.12, 0.35))
for e in exp_ok:
    sfx.append(("whoosh-short.mp3", e["t"] - 0.3 + 0.22 - 0.16, 0.2))
    if e.get("sfx") == "chime":
        sfx.append(("chime.mp3", e["t"] + 0.5, 0.35))
for p in prompts:
    sfx.append(("pop.mp3", p["t"] - 0.09, 0.3))
sfx_html = "\n".join(
    f'    <audio id="bd-sfx{i}" class="clip" src="assets/sfx/{f}" data-start="{max(0, round(t, 2))}" '
    f'data-duration="0.6" data-track-index="{9 + i % 2}" data-volume="{v}"></audio>'
    for i, (f, t, v) in enumerate(sorted(sfx, key=lambda x: x[1])))

exp_html = "\n".join(
    f'    <div id="bd-ex{i}" class="clip ex" data-start="{e["t"]}" data-duration="{e["d"]}" data-track-index="6">'
    f'<div class="ex-wrap exk-{e.get("kind", "headline")}">{exp_body(e)}</div></div>'
    for i, e in enumerate(exp_ok))
# captions sit bottom-centre; while a side-card explainer is up they move under its left column
def _cap_cls(c):
    for e in exp_ok:
        if e["t"] - 0.3 < c["t"] + c["d"] and c["t"] < e["t"] + e["d"]:
            return " cap-big" if e.get("kind") == "big" else " cap-side"   # clear of the corner camera card
    return ""
cap_html = "\n".join(
    f'    <div class="clip cap{_cap_cls(c)}" data-start="{r(c["t"])}" data-duration="{r(c["d"])}" '
    f'data-track-index="{11 + i % 2}"><span class="cap-in">{rich(c["text"])}</span></div>'
    for i, c in enumerate(captions))
TALK_CSS = "    .lt-card, .pr-card { bottom: 190px !important; }  /* talking-head: above the captions */" if TALK else ""
badges = [f for f in ffwd if f["x"] >= 3 and f["d"] >= 1.2]

badge_html = "\n".join(
    f'    <div id="bd-ff{i}" class="clip ff glass" data-start="{b["t"]}" data-duration="{b["d"]}" '
    f'data-track-index="4"><span class="ffi">▶▶</span> {b["x"]}×</div>'
    for i, b in enumerate(badges))
chap_html = "\n".join(
    f'    <div id="bd-ch{i}" class="clip chap" data-start="{c["t"]}" data-duration="4.2" data-track-index="5">'
    f'<div class="glass chap-card"><div class="chap-n">{c["n"]}</div>'
    f'<div class="chap-t">{c["title"]}</div>{"<div class=chap-s>" + c["sub"] + "</div>" if c.get("sub") else ""}</div></div>'
    for i, c in enumerate(chapters))

html = f"""<template>
  <style>
    @font-face {{
      font-family: "Bangla";
      src: local("Kohinoor Bangla Bold"), local("KohinoorBangla-Bold");
      font-weight: 700;
    }}
    #root {{
      position: absolute;
      inset: 0;
      overflow: hidden;
      font-family: "Oswald", sans-serif;
      color: #ffffff;
    }}
    #bd-room {{
      position: absolute;
      left: 0;
      top: 0;
      width: 1920px;
      height: 1080px;
      object-fit: cover;
    }}
    #bd-shade {{
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse at 30% 40%, rgba(70, 60, 120, 0.18), rgba(8, 8, 14, 0.55) 70%);
    }}
    #bd-scr-wrap {{
      position: absolute;
      left: {WX}px;
      top: {WY}px;
      width: {WW}px;
      height: {WH}px;
      border-radius: 18px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.14);
      box-shadow: 0 30px 70px rgba(0, 0, 0, 0.5);
      transform-origin: {WW / 2}px {WH / 2}px;
      z-index: 4;
    }}
    #bd-scr-inner {{
      position: absolute;
      left: 0;
      top: 0;
      width: {WW}px;
      height: {WH}px;
      transform-origin: 0 0;
    }}
    #bd-scr {{
      position: absolute;
      left: 0;
      top: 0;
      width: {WW}px;
      height: {WH}px;
      object-fit: cover;
    }}
    #bd-cam-wrap {{
      position: absolute;
      left: 0;
      top: 0;
      width: 1920px;
      height: 1080px;
      transform-origin: 960px 540px;
      z-index: 6;
      filter: drop-shadow(0 18px 34px rgba(0, 0, 0, 0.5));
    }}
    #bd-cam-inner {{
      position: absolute;
      inset: 0;
      transform-origin: 960px 420px;
    }}
    #bd-cam {{
      position: absolute;
      left: 0;
      top: 0;
      width: 1920px;
      height: 1080px;
      object-fit: cover;
    }}
    .glass {{
      background: rgba(28, 28, 36, 0.62);
      border: 1px solid rgba(255, 255, 255, 0.16);
      backdrop-filter: blur(18px);
      box-shadow: 0 18px 44px rgba(0, 0, 0, 0.35);
    }}
    .ff {{
      position: absolute;
      left: auto;
      right: 48px;
      top: 80px;
      z-index: 12;
      padding: 10px 26px 12px;
      border-radius: 999px;
      font-size: 40px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .ffi {{
      background: linear-gradient(90deg, #4aa3ff, #c06cff);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      margin-right: 6px;
    }}
    .bn {{
      font-family: "Bangla", sans-serif;
      font-weight: 700;
    }}
    .grad {{
      background: linear-gradient(90deg, #4aa3ff 0%, #8e7dff 55%, #c06cff 100%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }}
    .ex {{
      position: absolute;
      inset: 0;
      z-index: 13;
    }}
    .ex-wrap {{
      position: absolute;
      left: 90px;
      top: 210px;
      width: 730px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
    }}
    .exk-big {{
      left: 120px;
      top: 0;
      width: 1240px;
      height: 1080px;
      justify-content: center;
    }}
    .ex-big-t {{
      font-size: 132px;
      font-weight: 700;
      line-height: 1.06;
      text-transform: uppercase;
    }}
    .ex-big-t .bn {{
      text-transform: none;
      font-size: 0.8em;
    }}
    .cap {{
      position: absolute;
      left: 0;
      right: 0;
      bottom: 64px;
      text-align: center;
      z-index: 16;
    }}
    .cap-in {{
      display: inline-block;
      max-width: 1500px;
      padding: 10px 28px 14px;
      border-radius: 18px;
      background: rgba(10, 10, 16, 0.72);
      font-size: 58px;
      font-weight: 700;
      line-height: 1.25;
      text-shadow: 0 3px 12px rgba(0, 0, 0, 0.5);
    }}
    .cap-in .bn {{
      font-size: 0.92em;
    }}
    .cap-side {{
      left: 90px;
      right: auto;
      width: 760px;
      text-align: left;
    }}
    .cap-big {{
      right: 440px;
    }}
{TALK_CSS}
    .cap-side .cap-in {{
      font-size: 44px;
    }}
    .ex-title {{
      font-size: 84px;
      font-weight: 700;
      line-height: 1.12;
      text-transform: uppercase;
    }}
    .ex-title .bn {{
      text-transform: none;
      font-size: 0.82em;
    }}
    .ex-sub {{
      margin-top: 26px;
      font-size: 40px;
      color: #d6d6e2;
      line-height: 1.35;
    }}
    .ex-list, .ex-flow {{
      position: relative;
      margin-top: 34px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 18px;
    }}
    .ex-chip, .ex-step {{
      position: relative;
      padding: 14px 32px 16px 70px;
      border-radius: 18px;
      font-size: 46px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .ex-chip i {{
      position: absolute;
      left: 28px;
      top: 27px;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: linear-gradient(135deg, #4aa3ff, #c06cff);
    }}
    .ex-step b {{
      position: absolute;
      left: 22px;
      top: 22px;
      font-size: 26px;
      color: #9fb6ff;
    }}
    .ex-line {{
      position: absolute;
      left: 36px;
      top: 30px;
      bottom: 30px;
      width: 4px;
      border-radius: 2px;
      background: linear-gradient(#4aa3ff, #c06cff);
      transform-origin: 50% 0;
    }}
    .ex-stat {{
      font-size: 220px;
      font-weight: 700;
      line-height: 1;
      margin-top: 10px;
    }}
    .ex-compare {{
      display: flex;
      flex-direction: column;
      gap: 18px;
      margin-top: 34px;
      width: 100%;
    }}
    .ex-col {{
      min-width: 0;
      padding: 22px 26px 26px;
      border-radius: 20px;
      font-size: 42px;
      line-height: 1.3;
    }}
    .ex-col-l {{
      font-size: 26px;
      letter-spacing: 0.2em;
      color: #b9b9c8;
      margin-bottom: 10px;
      text-transform: uppercase;
    }}
    .ex-col-l .bn {{
      letter-spacing: 0;
      font-size: 1.25em;
    }}
    .ex-col:last-child {{
      border-color: rgba(160, 130, 255, 0.55);
    }}
    .lt {{
      position: absolute;
      inset: 0;
      z-index: 15;
    }}
    .lt-card {{
      position: absolute;
      left: 64px;
      bottom: 72px;
      padding: 18px 36px 20px;
      border-radius: 20px;
      border-left: 4px solid #8e7dff;
    }}
    .lt-name {{
      font-size: 54px;
      font-weight: 700;
      text-transform: uppercase;
      line-height: 1.05;
    }}
    .lt-line {{
      font-size: 28px;
      letter-spacing: 0.08em;
      color: #c8c8d8;
      margin-top: 4px;
    }}
    .pr {{
      position: absolute;
      inset: 0;
      z-index: 15;
    }}
    .pr-card {{
      position: absolute;
      left: 64px;
      bottom: 64px;
      max-width: 1180px;
      padding: 20px 30px 24px;
      border-radius: 20px;
      background: rgba(12, 12, 20, 0.86);
      border: 1px solid rgba(160, 130, 255, 0.55);
    }}
    .pr-label {{
      font-size: 24px;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: #9fb6ff;
      margin-bottom: 8px;
    }}
    .pr-text {{
      font-family: "JetBrains Mono", "Bangla", monospace;
      font-size: 32px;
      line-height: 1.4;
      color: #f2f2f8;
      white-space: pre-wrap;
    }}
    .chap {{
      position: absolute;
      inset: 0;
      z-index: 14;
    }}
    .chap-card {{
      position: absolute;
      left: 64px;
      bottom: 64px;
      padding: 22px 40px 26px;
      border-radius: 22px;
    }}
    .chap-n {{
      font-size: 30px;
      letter-spacing: 0.3em;
      color: #b9b9c8;
      font-weight: 500;
    }}
    .chap-t {{
      font-size: 76px;
      font-weight: 700;
      text-transform: uppercase;
      line-height: 1.05;
      background: linear-gradient(90deg, #ffffff 0%, #ffffff 40%, #9fb6ff 70%, #c06cff 100%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }}
    .chap-s {{
      font-family: "Bangla", sans-serif;
      font-size: 40px;
      font-weight: 700;
      color: #e6e6f0;
      margin-top: 4px;
    }}
  </style>
  <div id="root" data-composition-id="body" data-width="1920" data-height="1080">
    <img id="bd-room" data-color-grading="{GRADING}" src="assets/room.jpg" alt="" />
    <div id="bd-shade"></div>
    <div id="bd-scr-wrap">
      <div id="bd-scr-inner">
{"" if TALK else f'''        <video id="bd-scr" class="clip" src="assets/body_screen.mp4" data-start="0" data-duration="{TOTAL}"
          data-track-index="2" muted playsinline></video>'''}
      </div>
    </div>
    <div id="bd-cam-wrap">
      <div id="bd-cam-inner">
        <video id="bd-cam" data-color-grading="{CAM_GRADING}" class="clip" src="assets/body_cam.mp4" data-start="0" data-duration="{TOTAL}"
          data-track-index="1" muted playsinline></video>
      </div>
    </div>
    <audio id="bd-voice" class="clip" src="assets/body_voice.wav" data-start="0" data-duration="{TOTAL}"
      data-track-index="3" data-volume="1"></audio>
{badge_html}
{chap_html}
{exp_html}
{lt_html}
{prompt_html}
{cap_html}
{sfx_html}
  </div>
  <script>
    // Generated by tutorial-video-editor/scripts/build_body.py from work/edl.json — edit the EDL or the rules there.
    const SHOTS = {json.dumps(shot_list)};      // [start, end, "screen" | "face"]
    const ZOOMS = {json.dumps(zoom_list)};      // [t, scale, focusX, focusY] inside the page
    const FACE_CUTS = {json.dumps(face_cuts)};  // [t, punch-in scale] on jump cuts in face shots
    const CHAPTERS = {json.dumps([c["t"] for c in chapters])};
    const EXPLAINERS = {json.dumps([[e["t"], e["d"]] for e in exp_ok])};  // [start, length] — face shots only

    const tl = gsap.timeline({{ paused: true }});
    const CAM = {{
      full: {{ x: 0, y: 0, scale: 1, clipPath: "inset(0px 0px 0px 0px round 0px)" }},
      card: {{ x: {r(CX - 960)}, y: {r(CY - 540)}, scale: {r(CS, 4)}, clipPath: "inset(0px 0px 0px 0px round 90px)" }},
      side: {{ x: 391, y: 0, scale: 0.53, clipPath: "inset(0px 0px 0px 0px round 72px)" }},
    }};
    const SCR_ON = {{ opacity: 1, scale: 1, filter: "blur(0px)" }};
    const SCR_OFF = {{ opacity: 0, scale: 0.94, filter: "blur(12px)" }};

    // ── layout per shot ──
    SHOTS.forEach(([a, b, mode], i) => {{
      const prev = i ? SHOTS[i - 1][2] : null;
      if (i === 0) {{
        tl.set("#bd-cam-wrap", mode === "face" ? CAM.full : CAM.card, 0);
        tl.set("#bd-scr-wrap", mode === "face" ? SCR_OFF : SCR_ON, 0);
        return;
      }}
      if (mode === prev) return;
      const to = mode === "face" ? CAM.full : CAM.card, from = mode === "face" ? CAM.card : CAM.full;
      tl.fromTo("#bd-cam-wrap", {{ ...from }}, {{ ...to, duration: 0.6, ease: "expo.inOut", immediateRender: false }}, a - 0.3);
      tl.fromTo("#bd-scr-wrap", mode === "face" ? SCR_ON : SCR_OFF,
        {{ ...(mode === "face" ? SCR_OFF : SCR_ON), duration: 0.5, ease: "power3.inOut", immediateRender: false }}, a - 0.25);
    }});

    // ── zooms inside the page: centre the focus point, scale it ──
    tl.set("#bd-scr-inner", {{ x: 0, y: 0, scale: 1 }}, 0);
    ZOOMS.forEach(([t, s, fx, fy]) => {{
      const x = s === 1 ? 0 : {WW / 2} - s * fx * {WW};
      const y = s === 1 ? 0 : {WH / 2} - s * fy * {WH};
      tl.to("#bd-scr-inner", {{ x, y, scale: s, duration: 0.8, ease: "power2.inOut" }}, t);
    }});

    // ── punch-ins on jump cuts while on the face ──
    tl.set("#bd-cam-inner", {{ scale: 1 }}, 0);
    FACE_CUTS.forEach(([t, s]) => tl.set("#bd-cam-inner", {{ scale: s }}, t));
    SHOTS.forEach(([a, b, mode]) => {{ if (mode === "screen") tl.set("#bd-cam-inner", {{ scale: 1 }}, a); }});

    // ── badges and chapter cards ──
    gsap.utils.toArray(".ff").forEach((el) => {{
      const t = parseFloat(el.dataset.start);
      tl.fromTo(el, {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.6)" }}, t);
    }});
    gsap.utils.toArray(".chap-card").forEach((el, i) => {{
      const t = CHAPTERS[i];
      tl.fromTo(el, {{ opacity: 0, x: -40, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, t + 0.1);
      tl.to(el, {{ opacity: 0, filter: "blur(10px)", duration: 0.3, ease: "power2.in" }}, t + 3.8);
    }});

    // ── explainers: camera to a card on the right, the graphic builds on the left ──
    gsap.utils.toArray(".ex-wrap").forEach((el, i) => {{
      const [t, d] = EXPLAINERS[i];
      const lay = el.classList.contains("exk-big") ? CAM.card : CAM.side;
      tl.fromTo("#bd-cam-wrap", {{ ...CAM.full }}, {{ ...lay, duration: 0.6, ease: "expo.inOut", immediateRender: false }}, t - 0.3);
      tl.fromTo("#bd-cam-wrap", {{ ...lay }}, {{ ...CAM.full, duration: 0.6, ease: "expo.inOut", immediateRender: false }}, t + d - 0.35);
      const big = el.querySelector(".ex-big-t");
      if (big) tl.fromTo(big, {{ opacity: 0, scale: 0.9, filter: "blur(14px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, t + 0.2);
      const title = el.querySelector(".ex-title"), sub = el.querySelector(".ex-sub");
      if (title) tl.fromTo(title, {{ opacity: 0, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }}, t + 0.15);
      const parts = el.querySelectorAll(".ex-chip, .ex-step, .ex-col, .ex-stat");
      const step = parts.length ? Math.min(0.9, Math.max(0.35, (d - 2.2) / parts.length)) : 0;
      parts.forEach((p, j) => tl.fromTo(p, {{ opacity: 0, x: -30, filter: "blur(6px)" }},
        {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }}, t + 0.5 + j * step));
      const line = el.querySelector(".ex-line");
      if (line) tl.fromTo(line, {{ scaleY: 0 }}, {{ scaleY: 1, duration: Math.max(0.6, parts.length * step), ease: "power1.inOut" }}, t + 0.5);
      if (sub) tl.fromTo(sub, {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }}, t + 0.6 + parts.length * step);
      tl.to(el, {{ opacity: 0, filter: "blur(10px)", duration: 0.25, ease: "power2.in" }}, t + d - 0.3);
    }});

    // ── captions: a quick pop, no bounce — they must read, not perform ──
    gsap.utils.toArray(".cap-in").forEach((el) => {{
      const t = parseFloat(el.parentElement.dataset.start);
      tl.fromTo(el, {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: "power3.out" }}, t);
    }});

    // ── name lower-third and prompt cards ──
    gsap.utils.toArray(".lt-card, .pr-card").forEach((el) => {{
      const host = el.parentElement, t = parseFloat(host.dataset.start), d = parseFloat(host.dataset.duration);
      tl.fromTo(el, {{ opacity: 0, x: -40, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, t);
      tl.to(el, {{ opacity: 0, filter: "blur(10px)", duration: 0.3, ease: "power2.in" }}, t + d - 0.35);
    }});

    window.__timelines["body"] = tl;
  </script>
</template>
"""
open("../compositions/body.html", "w").write(html)
print(f"body.html: {TOTAL/60:.1f} min, {len(shot_list)} shots, {len(zoom_list)} zooms, "
      f"{len(face_cuts)} face punch-ins, {len(badges)} badges, {len(chapters)} chapters, {len(exp_ok)} explainers, "
      f"{len(prompts)} prompt cards, {len(captions)} captions{' (talking-head mode)' if TALK else ''}, {len(sfx)} sound effects, lower-third {'at ' + str(round(lt_t, 1)) + 's' if lt_t else 'none'}")
