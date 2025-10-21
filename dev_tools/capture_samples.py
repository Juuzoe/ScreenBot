import time, os, cv2, numpy as np
from mss import mss
from datetime import datetime

OUT="samples"
REGION=None
MON_IDX=1

os.makedirs(f"{OUT}/pos", exist_ok=True)
os.makedirs(f"{OUT}/neg", exist_ok=True)

sct = mss(); mon = sct.monitors[MON_IDX]

def grab():
    if REGION:
        l,t,w,h = REGION
        bbox = {"left": mon["left"]+l, "top": mon["top"]+t, "width": w, "height": h}
    else:
        bbox = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}
    return np.array(sct.grab(bbox))[:,:,:3]

print("Press P for positive, N for negative, Q to quit.")
try:
    import msvcrt as kbd
    def keypress():
        if kbd.kbhit(): return kbd.getch().decode("latin1").lower()
        return None
except:
    import sys, select
    def keypress():
        r,_,_ = select.select([sys.stdin], [], [], 0.1)
        return sys.stdin.read(1).lower() if r else None

while True:
    frame = grab()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    k = keypress()
    if k == "p":
        cv2.imwrite(f"{OUT}/pos/{ts}.png", frame); print("Saved POS")
    elif k == "n":
        cv2.imwrite(f"{OUT}/neg/{ts}.png", frame); print("Saved NEG")
    elif k == "q":
        print("Bye"); break
    time.sleep(0.05)
