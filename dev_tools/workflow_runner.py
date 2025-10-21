import os
import time
import yaml
import logging
import cv2
from typing import Any, Dict
from conditions import ScreenSampler, ConditionChecker
from actions import perform
from utils import setup_logging, ensure_dir, now_ts, image_hash

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def maybe_save(frame_bgr, rect, kind, score=None, out_dir="debug_dumps"):
    if frame_bgr is None or out_dir is None:
        return
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    name = f"{kind}_{now_ts()}_{image_hash(frame_bgr)}"
    if score is not None:
        name += f"_s{score:.2f}"
    path = os.path.join(out_dir, name + ".png")
    cv2.imwrite(path, frame_bgr)
    logging.info(f"Saved {kind} frame: {path}")

def run_step(step, defaults):
    cfg = {**defaults, **{k:v for k,v in step.items() if k not in ("name", "post_action_delay_ms")}}
    diag = (cfg.get("diagnostics") or {})
    save_on = set(diag.get("save_on", []))
    out_dir = diag.get("out_dir", "debug_dumps")

    poll_ms = int(cfg.get("poll_interval_ms", 250))
    timeout_s = int(cfg.get("max_wait_seconds", 45))
    region = cfg.get("region", None)
    mon_idx = int(cfg.get("monitor_index", 1))
    dry_run = bool(cfg.get("dry_run", False))

    sampler = ScreenSampler(monitor_index=mon_idx, region=region)
    checker = ConditionChecker(sampler, {"condition": cfg["condition"]})

    start = time.time()
    tries = 0
    logging.info(f"▶ Step: {step.get('name','(unnamed)')}")

    while True:
        tries += 1
        hit = checker.test()

        if hit and hit.get("met"):
            score = hit.get("score")
            if "hit" in save_on:
                maybe_save(hit.get("frame"), hit.get("frame_rect"), "hit", score, out_dir)
            logging.info(f"  ✓ Condition met (try {tries}) score={score}")
            perform(cfg["action"], hit, dry_run=dry_run)
            pad_ms = int(step.get("post_action_delay_ms", 0))
            if pad_ms > 0:
                time.sleep(pad_ms / 1000.0)
            return True

        if time.time() - start > timeout_s:
            logging.warning(f"  ✕ Timeout after {timeout_s}s.")
            if hit and "timeout" in save_on:
                maybe_save(hit.get("frame"), hit.get("frame_rect"), "timeout", None, out_dir)
            return False

        if "miss" in save_on and hit:
            maybe_save(hit.get("frame"), hit.get("frame_rect"), "miss", None, out_dir)

        time.sleep(poll_ms / 1000.0)

def main():
    setup_logging()
    import argparse
    p = argparse.ArgumentParser(description="Run a multi-step screen workflow")
    p.add_argument("workflow", help="Path to workflow YAML (e.g., workflows/my_flow.yaml)")
    args = p.parse_args()

    with open(args.workflow, "r", encoding="utf-8") as f:
        wf = yaml.safe_load(f)

    if not isinstance(wf, dict):
        logging.error(f"Invalid or empty workflow file: {args.workflow}")
        return

    defaults = wf.get("defaults", {})
    steps = wf.get("steps", [])
    if not steps:
        logging.error("No steps found in workflow.")
        return

    logging.info(f"Starting workflow: {args.workflow} ({len(steps)} steps)")
    for idx, step in enumerate(steps, 1):
        ok = run_step(step, defaults)
        if not ok:
            logging.error(f"Workflow stopped at step {idx}: {step.get('name','(unnamed)')}")
            return
    logging.info("Workflow completed successfully.")

if __name__ == "__main__":
    main()
