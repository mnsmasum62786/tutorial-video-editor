"""Cut a short list of source ranges into frame-exact clips (fast seeking, for the intro).

  python cut_clips.py <name> <a:b> [<a:b> ...]  [--screen a:b]

Writes ../assets/<name>_cam.mp4 and ../assets/<name>_voice.wav (ranges joined in order) and,
with --screen, ../assets/<name>_screen.mp4 for one range. Prints each clip's output start.
"""
import os, sys, subprocess, numpy as np, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SRC = os.environ.get("TVE_SRC") or sys.exit("set TVE_SRC to the recording prefix, e.g. '/path/My talk_' (…_Camera.mp4, …_Screen.mp4, …_Microphone.mp3)")
FPS, SR = 25, 48000
SPF = SR // FPS
name = sys.argv[1]
args = sys.argv[2:]
screen = None
if "--screen" in args:
    i = args.index("--screen"); screen = args[i + 1]; args = args[:i] + args[i + 2:]
ranges = [tuple(int(round(float(v) * FPS)) for v in r.split(":")) for r in args]

def clip(src, a, n, out, vf):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a / FPS:.3f}", "-i", src, "-frames:v", str(n),
                    "-vf", vf, "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-g", str(FPS), "-pix_fmt", "yuv420p", out], check=True)

os.makedirs("clips", exist_ok=True)
lst = open("clips/list.txt", "w")
t = 0
for i, (a, b) in enumerate(ranges):
    clip(SRC + "Camera.mp4", a, b - a, f"clips/{name}_{i}.mp4", "setpts=PTS-STARTPTS")
    lst.write(f"file '{name}_{i}.mp4'\n")
    print(f"clip {i}: source {a / FPS:.2f}-{b / FPS:.2f}  ->  out {t / FPS:.2f}-{(t + b - a) / FPS:.2f}")
    t += b - a
lst.close()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-i", "clips/list.txt", "-c", "copy",
                f"../assets/{name}_cam.mp4"], check=True)

raw = "mic48.f32"
if not os.path.exists(raw):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC + "Microphone.mp3", "-ac", "1", "-ar", str(SR),
                    "-f", "f32le", raw], check=True)
x = np.memmap(raw, np.float32, "r")
fade = np.linspace(0, 1, int(SR * 0.006), dtype=np.float32)
parts = []
for a, b in ranges:
    p = np.array(x[a * SPF:b * SPF], np.float32)
    p[:len(fade)] *= fade; p[-len(fade):] *= fade[::-1]
    parts.append(p)
y = np.concatenate(parts)
tmp = f"clips/{name}_raw.wav"
with wave.open(tmp, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.clip(y * 32767, -32768, 32767).astype(np.int16).tobytes())
from voice_chain import finish_voice            # same voice sound as the body
I, gain = finish_voice(tmp, f"../assets/{name}_voice.wav", SR)
print(f"total {t / FPS:.2f}s, voice {I:.1f} LUFS before, gain {gain:+.1f} dB")

if screen:
    a, b = (int(round(float(v) * FPS)) for v in screen.split(":"))
    clip(SRC + "Screen.mp4", a, b - a, f"../assets/{name}_screen.mp4",
         "setpts=PTS-STARTPTS,crop=3420:1772:0:224,scale=2560:1326:flags=lanczos")
    print(f"screen {a / FPS:.2f}-{b / FPS:.2f} ({(b - a) / FPS:.2f}s)")
