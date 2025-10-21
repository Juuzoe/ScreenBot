import sys, time, os
import yaml
import cv2
import numpy as np

from conditions import ScreenSampler, ConditionChecker

def main():
    yaml_path = sys.argv[1] if len(sys.argv) > 1 else "workflows/two_phase.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        wf = yaml.safe_load(f)

    defaults = wf.get("defaults", {})
    phase1   = wf["phase1"]
    steps    = phase1["steps"]

    # pick the first step named "P1 Start" (or first step)
    step = None
    for s in steps:
        if s.get("name","").lower().strip() in ("p1 start","start"):
            step = s
            break
    if step is None:
        step = steps[0]

    cond_cfg = step["condition"]
    region   = step.get("region", defaults.get("region", None))
    mon_idx  = int(defaults.get("monitor_index", 1))

    print(f"Testing step: {step.get('name')}")
    print(f"Template: {cond_cfg.get('template_path')}")
    print(f"Confidence: {cond_cfg.get('confidence')}, multiscale: {cond_cfg.get('multiscale')}")
    print(f"Monitor index: {mon_idx}, region: {region}")

    sampler = ScreenSampler(monitor_index=mon_idx, region=region)
    checker = ConditionChecker(sampler, {"condition": cond_cfg})

    # Grab once, test once (exactly like runner does)
    res = checker.test()

    # We also want to see the "best attempt" even on miss, so we re-run a minimal internal match
    # But the checker already returns helpful fields on miss:
    frame = res.get("frame")
    frame_rect = res.get("frame_rect")
    H, W = frame.shape[:2]

    if res.get("met"):
        x, y, w, h = res["x"], res["y"], res["w"], res["h"]
        score = res["score"]; scale = res.get("scale", 1.0)
        print(f"\n✅ HIT: score={score:.3f}, scale={scale:.2f}, rect=({x},{y},{w},{h})")
        out = frame.copy()
        cv2.rectangle(out, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cx, cy = x + w//2, y + h//2
        cv2.circle(out, (cx, cy), 4, (0, 255, 0), -1)
        out_path = "probe_hit.png"
        cv2.imwrite(out_path, out)
        print(f"Saved annotated hit to {out_path}")
    else:
        best = res.get("best_loc_abs", (0,0))
        best_score = res.get("best_score", -1.0)
        best_scale = res.get("best_scale", 1.0)
        print(f"\n❌ MISS: best_score={best_score:.3f}, best_scale={best_scale:.2f}, best_loc_abs={best}")

        # Draw a small box around best_loc_abs to see *where* it wanted to match
        out = frame.copy()
        bx, by = best
        # Try to draw a 120x80 box for visibility (unknown template size here)
        cv2.rectangle(out, (max(0,bx), max(0,by)), (min(W-1,bx+120), min(H-1,by+80)), (0, 0, 255), 2)
        out_path = "probe_miss.png"
        cv2.imwrite(out_path, out)
        print(f"Saved annotated miss to {out_path}")

    # Also print what the system thinks the capture area is
    print(f"\nCapture rect (absolute): {frame_rect}  | Frame size: {W}x{H}")

if __name__ == "__main__":
    main()
