"""Write compositions/outro.html — the 20 s YouTube end screen — from assets/outro-template.html.

Run inside <project>/work. Fields come from work/channel.json (else the skill's assets/channel.json) and the
room grade in work/room_grading.attr, so the end screen sits on the same blurred room as the intro and body.
"""
import html, json, os

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ch = json.load(open("channel.json" if os.path.exists("channel.json") else os.path.join(SKILL, "assets", "channel.json")))
s = open(os.path.join(SKILL, "assets", "outro-template.html")).read()
for key, val in {"NAME": ch["name"], "LINE": ch.get("line", ""), "CTA": ch.get("cta", "SUBSCRIBE"),
                 "OUTRO_LINE": ch.get("outro_line", "WATCH NEXT")}.items():
    s = s.replace("{{" + key + "}}", html.escape(val))
s = s.replace("{{GRADING}}", open("room_grading.attr").read())
os.makedirs("../compositions", exist_ok=True)
open("../compositions/outro.html", "w").write(s)
print("outro.html: 20 s end screen for", ch["name"])
