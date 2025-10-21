import cv2
import numpy as np
from mss import mss

class ScreenSampler:
    """Grab a screenshot of the full 1920x1080 screen, or a region (left, top, width, height)."""
    def __init__(self, region=None):
        self.region = region  # tuple or None

    def grab(self):
        with mss() as sct:
            if self.region:
                left, top, width, height = self.region
                box = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
            else:
                box = {"left": 0, "top": 0, "width": 1920, "height": 1080}
            shot = np.array(sct.grab(box))  # BGRA
            bgr = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
            return bgr

class ConditionChecker:
    """
    Simple template match.
    Config shape:
      {"condition": {"template_path": "assets/thing.png", "confidence": 0.9}}
    """
    def __init__(self, sampler: ScreenSampler, config: dict):
        self.sampler = sampler
        cond = config.get("condition", {})
        self.confidence = float(cond.get("confidence", 0.9))
        path = cond.get("template_path", "")
        self.template = cv2.imread(path, cv2.IMREAD_COLOR)
        if self.template is None:
            raise FileNotFoundError(f"Template not found: {path}")

    def test(self):
        frame = self.sampler.grab()
        res = cv2.matchTemplate(frame, self.template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(res)

        h, w = self.template.shape[:2]
        rect = (int(max_loc[0]), int(max_loc[1]), int(w), int(h))
        met = bool(max_val >= self.confidence)

        return {
            "met": met,
            "score": float(max_val),
            "rect": rect,
            "frame": frame,
        }
