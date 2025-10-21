import time, random, logging, yaml, argparse
from typing import Dict, Any, List
from conditions import ScreenSampler, ConditionChecker
from actions import perform
from utils import setup_logging

def run_step(step: Dict[str, Any], defaults: Dict[str, Any],
             step_time_min: float, step_time_max: float) -> bool:
    cfg = {**defaults, **{k:v for k,v in step.items() if k not in ("name", "post_action_delay_ms")}}
    poll_ms   = int(cfg.get("poll_interval_ms", 200))
    timeout_s = int(cfg.get("max_wait_seconds", 30))
    region    = cfg.get("region", None)
    mon_idx   = int(cfg.get("monitor_index", 1))
    dry_run   = bool(cfg.get("dry_run", False))

    sampler = ScreenSampler(monitor_index=mon_idx, region=region)
    checker = ConditionChecker(sampler, {"condition": cfg["condition"]})

    name = step.get("name","(unnamed)")
    logging.info(f"▶ {name}")
    start_wait = time.perf_counter()

    while True:
        hit = checker.test()
        if hit and hit.get("met"):
            perform(cfg["action"], hit, dry_run=dry_run)
            elapsed = time.perf_counter() - start_wait
            target  = random.uniform(step_time_min, step_time_max)
            if target > elapsed:
                time.sleep(target - elapsed)
            logging.info(f"  ✓ {name} (elapsed={elapsed:.3f}s, target≈{target:.2f}s)")
            return True
        if (time.perf_counter() - start_wait) > timeout_s:
            logging.warning(f"  ✕ {name} timed out at {timeout_s}s")
            return False
        time.sleep(poll_ms/1000.0)

def run_phase(phase_cfg: Dict[str, Any], defaults: Dict[str, Any],
              repeats_override: int,
              step_min: float, step_max: float,
              cycle_min: float, cycle_max: float,
              label: str) -> bool:
    repeats = int(repeats_override if repeats_override is not None else phase_cfg.get("repeats", 1))
    steps: List[Dict[str, Any]] = phase_cfg.get("steps", [])
    if not steps:
        logging.error(f"{label}: no steps.")
        return False

    logging.info(f"{label}: repeats={repeats} | per-step {step_min:.2f}-{step_max:.2f}s | cycle cap {cycle_min:.2f}-{cycle_max:.2f}s")

    for cycle in range(1, repeats+1):
        logging.info(f"{label} — Cycle {cycle}/{repeats}")
        cycle_start = time.perf_counter()

        for i, step in enumerate(steps, 1):
            if not run_step(step, defaults, step_min, step_max):
                logging.error(f"{label}: stopped at step {i} in cycle {cycle}.")
                return False

        elapsed = time.perf_counter() - cycle_start
        if elapsed < cycle_min:
            pad = cycle_min - elapsed
            logging.info(f"{label}: cycle {cycle} {elapsed:.2f}s → padding {pad:.2f}s")
            time.sleep(pad)
        elif elapsed > cycle_max:
            logging.warning(f"{label}: cycle {cycle} {elapsed:.2f}s (> {cycle_max:.2f}s)")
    return True

def main():
    setup_logging()
    ap = argparse.ArgumentParser(description="Run two-phase workflow (different timings per phase).")
    ap.add_argument("yaml_path", help="Path to two_phase.yaml")

    # Per-phase repeats (optional overrides)
    ap.add_argument("--p1-repeats", type=int, default=None)
    ap.add_argument("--p2-repeats", type=int, default=None)

    # Per-phase per-step pacing
    ap.add_argument("--p1-step-min", type=float, default=0.50)
    ap.add_argument("--p1-step-max", type=float, default=0.55)
    ap.add_argument("--p2-step-min", type=float, default=0.45)
    ap.add_argument("--p2-step-max", type=float, default=0.50)

    # Shared cycle caps (keep overall time similar)
    ap.add_argument("--cycle-min", type=float, default=4.0)
    ap.add_argument("--cycle-max", type=float, default=4.4)
    args = ap.parse_args()

    with open(args.yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict) or "phase1" not in cfg or "phase2" not in cfg:
        logging.error("YAML must include 'phase1' and 'phase2'.")
        return

    defaults = cfg.get("defaults", {})
    logging.info(f"YAML: {args.yaml_path}")

    ok = run_phase(cfg["phase1"], defaults, args.p1_repeats,
                   args.p1_step_min, args.p1_step_max,
                   args.cycle_min, args.cycle_max, "Phase 1")
    if not ok:
        return
    logging.info(">>> Phase 1 complete. Moving to Phase 2…")

    run_phase(cfg["phase2"], defaults, args.p2_repeats,
              args.p2_step_min, args.p2_step_max,
              args.cycle_min, args.cycle_max, "Phase 2")

if __name__ == "__main__":
    main()
