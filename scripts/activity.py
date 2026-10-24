# Reads gray 640x374 frames at 2 fps from stdin; writes per-frame screen-change stats as JSON lines.
import sys, json, numpy as np, cv2
W, H = 640, 374
out = open(sys.argv[1], "w")
prev = None; i = 0
while True:
    buf = sys.stdin.buffer.read(W * H)
    if len(buf) < W * H: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W)
    rec = {"t": round(i / 2, 2)}
    if prev is not None:
        m = (cv2.absdiff(f, prev) > 24).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        frac = float(m.mean())
        rec["frac"] = round(frac, 5)
        if frac > 0:
            ys, xs = np.nonzero(m)
            rec["box"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            rec["cx"] = round(float(xs.mean()) / W, 3); rec["cy"] = round(float(ys.mean()) / H, 3)
    out.write(json.dumps(rec) + "\n"); out.flush()
    prev = f; i += 1
