import time
import random
from core.conditions import ScreenSampler, ConditionChecker
from core.actions import perform

def run_step(step: dict, defaults: dict, step_min: float, step_max: float, log):
    """
    Run one step:
      - wait for a condition
      - perform action
      - pad to a per-step duration window
    """
    # Merge defaults with the step (step wins)
    cfg = dict(defaults or {})
    for k, v in step.items():
        if k != "name":
            cfg[k] = v

    poll_ms   = int(cfg.get("poll_interval_ms", 200))
    timeout_s = int(cfg.get("max_wait_seconds", 25))
    region    = cfg.get("region", None)
    dry_run   = bool(cfg.get("dry_run", False))

    sampler = ScreenSampler(region=region)
    checker = ConditionChecker(sampler, {"condition": cfg["condition"]})

    name = step.get("name", "step")
    log(f"Step: {name}")
    started = time.perf_counter()
    match = None

    # Keep checking until timeout
    while (time.perf_counter() - started) < timeout_s:
        result = checker.test()
        if result and result["met"]:
            match = result
            break
        time.sleep(poll_ms / 1000.0)

    if not match:
        log(f"  timeout after {timeout_s}s")
        return False

    perform(cfg["action"], match, dry_run=dry_run)

    # pad to keep the rhythm between actions
    elapsed = time.perf_counter() - started
    target = random.uniform(step_min, step_max)
    if target > elapsed:
        time.sleep(target - elapsed)
    log(f"  done (score={match['score']:.3f})")
    return True

def run_phase(label: str, phase_cfg: dict, defaults: dict,
              step_min: float, step_max: float, repeats: int,
              cycle_min: float, cycle_max: float, log) -> bool:
    """
    Run a group of steps several times (a "phase").
    """
    steps = (phase_cfg or {}).get("steps", [])
    if not steps:
        log(f"{label}: no steps")
        return False

    log(f"{label}: repeats={repeats}, per_step={step_min:.2f}-{step_max:.2f}s, cycle_caps={cycle_min:.2f}-{cycle_max:.2f}s")

    for cycle in range(1, repeats + 1):
        log(f"{label} — cycle {cycle}/{repeats}")
        cycle_start = time.perf_counter()

        for step in steps:
            ok = run_step(step, defaults, step_min, step_max, log)
            if not ok:
                log(f"{label}: stopped during steps")
                return False

        # keep overall cycle timing reasonable
        total = time.perf_counter() - cycle_start
        if total < cycle_min:
            time.sleep(cycle_min - total)
        # if over cycle_max, just report it; we don't try to "fix" it
        if total > cycle_max:
            log(f"{label}: cycle took {total:.2f}s (> {cycle_max:.2f}s)")

    return True
