import os
import ttkbootstrap as tb
from tkinter import filedialog, messagebox
from tkinter import StringVar, Text
from ui.theme import init_style
from ui.controller import Controller

DEFAULT_WORKFLOW = os.path.abspath("workflows/two_phase.yaml")

class App(tb.Window):
    def __init__(self):
        super().__init__(themename="journal")

        style, palette = init_style()
        self._style = style          
        self.palette = palette

        self.title("ScreenBot — Control Center")
        self.geometry("1024x700")
        self.minsize(900, 620)

        self.yaml_var = StringVar(value=DEFAULT_WORKFLOW)
        self.logbox: Text | None = None

        
        self.ctrl = Controller(
            log_callback=self._log,
            state_callback=self._set_running_ui,
            get_yaml_path=lambda: self.yaml_var.get()
        )

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=240)
        self.grid_columnconfigure(1, weight=1)

        # left side
        rail = tb.Frame(self, style="Card.TFrame")
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_rowconfigure(99, weight=1)  

        tb.Label(rail, text="ScreenBot", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(18, 10)
        )
        #looks crazy but i just copied it from from my last project, so sorry if you are reading this
        box = tb.Frame(rail, style="Card.TFrame")
        box.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        tb.Label(box, text="Workflow", style="TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        tb.Entry(box, textvariable=self.yaml_var, width=26).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        box.grid_columnconfigure(0, weight=1)
        tb.Button(box, text="Browse", command=self._browse, bootstyle="secondary").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 12))

        controls = tb.Frame(rail, style="Card.TFrame")
        controls.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.btn_start = tb.Button(controls, text="Start", command=self._start, bootstyle="success-outline", width=16)
        self.btn_stop  = tb.Button(controls, text="Stop",  command=self._stop,  bootstyle="danger-outline", width=16, state="disabled")
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        self.btn_stop.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

        # right side
        main = tb.Frame(self, style="TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        header = tb.Frame(main, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        tb.Label(header, text="Activity", style="Title.TLabel").pack(side="left", padx=12, pady=10)

        body = tb.Frame(main, style="Card.TFrame")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.logbox = tb.ScrolledText(body)
        self.logbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.logbox.configure(background=self.palette["logbg"], foreground=self.palette["text"])

        footer = tb.Frame(main, style="Card.TFrame")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        tb.Label(footer, text="Alt+Shift+S → Start   •   Alt+Shift+X → Stop", style="Muted.TLabel").pack(side="left", padx=12, pady=10)
        tb.Button(footer, text="Exit", command=self._on_close, bootstyle="secondary-outline").pack(side="right", padx=12, pady=8)

    # actions
    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml;*.yml")])
        if path:
            self.yaml_var.set(path)

    def _start(self):
        self.ctrl.start(self.yaml_var.get().strip())

    def _stop(self):
        self.ctrl.stop()

    # logs
    def _log(self, msg: str):
        if not self.logbox:
            return
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")

    def _set_running_ui(self, running: bool):
        self.btn_start.configure(state=("disabled" if running else "normal"))
        self.btn_stop.configure(state=("normal" if running else "disabled"))
        if not running:
            self._log("Finished.")

    def _on_close(self):
        try:
            self.ctrl.shutdown()
        except Exception:
            pass
        self.destroy()

def run_app():
    app = App()
    app.mainloop()
