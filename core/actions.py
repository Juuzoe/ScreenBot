import time
import random
import pyautogui as pag

def move_mouse_like_a_person(x, y, base_time=0.28, wiggle=0.18):
    """Move the mouse to (x, y) with a tiny bit of randomness."""
    duration = max(0.05, base_time + random.uniform(-wiggle, wiggle))
    dx = random.uniform(-2, 2)
    dy = random.uniform(-2, 2)
    pag.moveTo(x + dx, y + dy, duration=duration)

def perform_action(action, match_info, dry_run=False):
    """
    Do something after a match.
    Supported actions:
      - {"type": "click"}
      - {"type": "approach_click"}
      - {"type": "sleep", "seconds": 1.0}
    Look into example yaml for more examples of actions
    """
    if not action:
        return

    action_type = (action.get("type") or "click").lower()

    if action_type in ("click", "approach_click"):
        x, y, w, h = match_info.get("rect", (0, 0, 0, 0))
        cx = x + w // 2
        cy = y + h // 2
        if not dry_run:
            if action_type == "approach_click":
                move_mouse_like_a_person(cx, cy, base_time=0.35, wiggle=0.25)
            else:
                move_mouse_like_a_person(cx, cy)
            pag.click()
        # you can delete if your actions doesnt require human detection
        time.sleep(random.uniform(0.08, 0.22))
        return

    if action_type == "sleep":
        time.sleep(float(action.get("seconds", 1.0)))
        return

# Legacy name some files import
perform = perform_action
