import os
import yaml
import threading
from pynput import keyboard
from core.workflow_cycle_runner import run_phase

#change hotkeys here if u want
DEFAULT_START = "<alt>+<shift>+s"
DEFAULT_STOP  = "<alt>+<shift>+x"

class HotkeyManager:
    """Global hotkeys for start/stop."""
    def __init__(self, on_start, on_stop, start_combo=DEFAULT_START, stop_combo=DEFAULT_STOP):
        self.on_start = on_start
        self.on_stop  = on_stop
        self.start_combo = start_combo
        self.stop_combo  = stop_combo
        self.listener = None
        self._mount()

    def _mount(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
        mapping = {self.start_combo: self.on_start, self.stop_combo: self.on_stop}
        self.listener = keyboard.GlobalHotKeys(mapping)
        self.listener.start()

    def update(self, start_combo=None, stop_combo=None):
        if start_combo: self.start_combo = start_combo
        if stop_combo:  self.stop_combo  = stop_combo
        self._mount()

    def stop(self):
        try:
            self.listener.stop()
        except Exception:
            pass


class Controller:
    """
    Keeps UI thin:
      - reads YAML
      - runs phases
      - threads + logging
    """
    def __init__(self, log_callback, state_callback, get_yaml_path=None):
        self.log = log_callback
        self.set_state = state_callback
        self.get_yaml_path = get_yaml_path
        self.worker = None
        self.stop_flag = threading.Event()
        self.hotkeys = HotkeyManager(self._hotkey_start, self.stop)

    # UI start (button)
    def start(self, yaml_path: str):
        if self.worker and self.worker.is_alive():
            self.log("Already running.")
            return
        if not os.path.isfile(yaml_path):
            self.log("YAML not found.")
            return
        self.stop_flag.clear()
        self.worker = threading.Thread(target=self._run_file, args=(yaml_path,), daemon=True)
        self.set_state(running=True)
        self.log(f"Starting: {os.path.basename(yaml_path)}")
        self.worker.start()

    # Hotkey start (no button)
    def _hotkey_start(self):
        if self.worker and self.worker.is_alive():
            self.log("Already running. Press Alt+Shift+X to stop.")
            return
        if not callable(self.get_yaml_path):
            self.log("No YAML selected.")
            return
        path = (self.get_yaml_path() or "").strip()
        if not path or not os.path.isfile(path):
            self.log("YAML not found.")
            return
        self.start(path)

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.stop_flag.set()
            self.log("Stop requested.")
        else:
            self.log("Nothing to stop.")

    def _run_file(self, yaml_path: str):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                self.log("Invalid YAML structure.")
                return

            defaults = data.get("defaults", {})

            # Preferred: phases as dict
            phases = data.get("phases")
            if isinstance(phases, dict):
                for name, phase in phases.items():  # order preserved
                    if self.stop_flag.is_set():
                        break
                    self._run_phase_block(str(name), phase, defaults)
                return

            # Also accept: phases as list
            if isinstance(phases, list):
                for i, phase in enumerate(phases, 1):
                    if self.stop_flag.is_set():
                        break
                    name = phase.get("name", f"Phase {i}")
                    self._run_phase_block(name, phase, defaults)
                return

            # Legacy: phase1 / phase2
            if "phase1" in data and "phase2" in data:
                self._run_phase_block("phase1", data["phase1"], defaults)
                if not self.stop_flag.is_set():
                    self._run_phase_block("phase2", data["phase2"], defaults)
                return

            self.log("YAML must have 'phases' (dict or list), or 'phase1' and 'phase2'.")
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.set_state(running=False)

    def _run_phase_block(self, label, phase_cfg, defaults):
        pmin   = float(phase_cfg.get("step_min_sec", 0.50))
        pmax   = float(phase_cfg.get("step_max_sec", 0.55))
        cycmin = float(phase_cfg.get("cycle_min_sec", 4.0))
        cycmax = float(phase_cfg.get("cycle_max_sec", 4.4))
        reps   = int(phase_cfg.get("repeats", 1))
        ok = run_phase(label, phase_cfg, defaults, pmin, pmax, reps, cycmin, cycmax, self.log)
        if not ok:
            self.log(f"Stopped in {label}")

    def shutdown(self):
        try:
            self.hotkeys.stop()
        except Exception:
            pass
