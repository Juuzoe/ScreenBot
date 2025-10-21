import cv2, numpy as np
from mss import mss

# Path to your button image (tight crop)
TEMPLATE_PATH = "assets/btn_start.png"

# Monitor index (1 = primary monitor, 2+ = extra monitors)
MONITOR_INDEX = 1

# Try multiple scales in case DPI/zoom differs
SCALES = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]

# Load template
templ = cv2.imread(TEMPLATE_PATH)
if templ is None:
    raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

sct = mss()
mon = sct.monitors[MONITOR_INDEX]
screenshot = np.array(sct.grab({
    "left": mon["left"],
    "top": mon["top"],
    "width": mon["width"],
    "height": mon["height"]
}))[:, :, :3]

scr_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

best = None
for s in SCALES:
    tw, th = int(templ.shape[1]*s), int(templ.shape[0]*s)
    if tw < 5 or th < 5:
        continue
    resized = cv2.resize(templ, (tw, th), interpolation=cv2.INTER_AREA)
    res = cv2.matchTemplate(scr_gray, cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if not best or max_val > best[0]:
        best = (max_val, max_loc, (tw, th), s)

if best:
    score, loc, size, scale = best
    print(f"Best score = {score:.3f}")
    print(f"Location = {loc} (top-left corner of match)")
    print(f"Template size used = {size} (w,h)")
    print(f"Scale = {scale}")
else:
    print("No match found at any scale.")
