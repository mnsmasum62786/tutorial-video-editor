"""Bake privacy blur into a screen video from OCR detections (ocr_redact output).

  python redact_bake.py <in.mp4> <ocr.jsonl> <step> <out.mp4> [hold_frames]

step: the OCR sampled every <step>-th frame (file 000123.jpg = frame 123*step).
A token seen in two samples up to ~1 s apart gets a box interpolated on every frame between
(covers scrolling); every detection is also held +-hold frames. Boxes are padded, then the
region is downsampled 10x and gaussian-blurred, so no zoom level can read it.
"""
import sys, json, os, re, subprocess, difflib, numpy as np, cv2

src, ocr, step, dst = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
HOLD = int(sys.argv[5]) if len(sys.argv) > 5 else max(3, step + 2)
LOOK = max(1, 25 // step)                      # look ahead about one second of samples

probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=width,height,nb_read_packets", "-of", "csv=p=0", src],
                       capture_output=True, text=True).stdout.strip().split(",")
W, H, N = int(probe[0]), int(probe[1]), int(probe[2])

samples = {}
for line in open(ocr):
    d = json.loads(line)
    k = int(re.search(r"(\d+)\.\w+$", d["f"]).group(1))
    samples[k] = [(m[0] * W, m[1] * H, m[2] * W, m[3] * H, m[4], m[5]) for m in d["m"]]

def norm(t):
    return re.sub(r"\s+", "", t.lower())

frames = {}
def add(f, box):
    if 0 <= f < N:
        frames.setdefault(f, []).append(box)

keys = sorted(samples)
for k in keys:
    for (x, y, w, h, kind, txt) in samples[k]:
        f0 = k * step
        for df in range(-HOLD, HOLD + 1):
            add(f0 + df, (x, y, w, h))
        # follow the same token to a later sample and fill the frames between
        for j in range(1, LOOK + 1):
            nxt = samples.get(k + j)
            if not nxt:
                continue
            best = None
            for (x2, y2, w2, h2, k2, t2) in nxt:
                if k2 != kind:
                    continue
                if difflib.SequenceMatcher(None, norm(txt), norm(t2)).ratio() < 0.75:
                    continue
                dist = abs(x2 - x) + abs(y2 - y)
                if best is None or dist < best[0]:
                    best = (dist, (x2, y2, w2, h2))
            if best:
                x2, y2, w2, h2 = best[1]
                f1 = (k + j) * step
                # scrolling eases, so a straight-line guess lags the text: cover the whole area
                # the token swept through between the two samples
                ux0, uy0 = min(x, x2), min(y, y2)
                ux1, uy1 = max(x + w, x2 + w2), max(y + h, y2 + h2)
                for f in range(f0, f1 + 1):
                    add(f, (ux0, uy0, ux1 - ux0, uy1 - uy0))
                break

# manual boxes for text OCR cannot read (cut by the frame edge): EXTRA_BOXES=file.json
# [{"from": frame, "to": frame, "box": [x, y, w, h]}]  (box normalised to the frame)
extra = os.environ.get("EXTRA_BOXES")
if extra:
    for e in json.load(open(extra)):
        x, y, w, h = e["box"]
        for f in range(e["from"], min(N, e["to"] + 1)):
            add(f, (x * W, y * H, w * W, h * H))

def blur_region(img, x, y, w, h):
    th = min(h, 28)                       # pad by text height, not by tall (name + avatar) boxes
    px, py = max(8, 0.6 * th), max(6, 0.35 * th)
    x0, y0 = int(max(0, x - px)), int(max(0, y - py))
    x1, y1 = int(min(W, x + w + px)), int(min(H, y + h + py))
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    reg = img[y0:y1, x0:x1]
    small = cv2.resize(reg, (max(1, (x1 - x0) // 10), max(1, (y1 - y0) // 10)), interpolation=cv2.INTER_AREA)
    big = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big, (0, 0), 6)
    img[y0:y1, x0:x1] = big

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox", "-i", src, "-f", "rawvideo",
                        "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", "25", "-i", "-", "-c:v", "h264_videotoolbox", "-b:v", "18M", "-g", "25",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
size = W * H * 3
STRIP = int(os.environ.get("EDGE_STRIP", "28"))
f = touched = 0
while True:
    buf = dec.stdout.read(size)
    if len(buf) < size:
        break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    # text scrolling off the bottom edge is cut in half: OCR cannot read it, a viewer can guess it
    strip = img[H - STRIP:H]
    small = cv2.resize(strip, (W // 10, max(1, STRIP // 10)), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(cv2.resize(small, (W, STRIP), interpolation=cv2.INTER_LINEAR), (0, 0), 6)
    a = np.clip(np.arange(STRIP, dtype=np.float32) / 8, 0, 1)[:, None, None]   # 8 px fade, then fully blurred
    img[H - STRIP:H] = (strip * (1 - a) + blurred * a).astype(np.uint8)
    if f in frames:
        for b in frames[f]:
            blur_region(img, *b)
        touched += 1
    buf = img.tobytes()
    enc.stdin.write(buf)
    f += 1
enc.stdin.close(); enc.wait(); dec.wait()
print(f"{dst}: {f} frames ({N} expected), {touched} frames blurred, "
      f"{sum(len(v) for v in samples.values())} detections in {len(samples)} samples")
