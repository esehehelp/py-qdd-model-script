import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

class ParameterPanel(ttk.Labelframe):
    def __init__(self, master, param_defs: Dict, *args, **kwargs):
        super().__init__(master, *args, text='モーターパラメータ', **kwargs)
        self.param_defs = param_defs
        self.vars: Dict[str, tk.Variable] = {}
        self._build()

    def _build(self):
        row = 0
        for section, fields in self.param_defs.items():
            ttk.Label(self, text=section, font=('TkDefaultFont', 10, 'bold')).grid(row=row, columnspan=4, sticky='w', pady=(8,2))
            row += 1
            items = list(fields.items())
            for i, (key, value) in enumerate(items):
                r = row + (i // 2)
                c = (i % 2) * 2
                ttk.Label(self, text=value[0]).grid(row=r, column=c, sticky='w', padx=5, pady=2)
                if len(value) > 2 and isinstance(value[2], list):
                    var = tk.StringVar(value=value[1])
                    widget = ttk.Combobox(self, textvariable=var, values=value[2], width=10)
                else:
                    var = tk.DoubleVar(value=value[1])
                    widget = ttk.Entry(self, textvariable=var, width=12)
                widget.grid(row=r, column=c+1, sticky='e', padx=5, pady=2)
                self.vars[key] = var
            row += (len(items)+1)//2

    def get_params(self):
        params = {}
        param_labels = {k: v[0] for section in self.param_defs.values() for k, v in section.items()}

        for key, var in self.vars.items():
            try:
                params[key] = var.get()
            except tk.TclError:
                label = param_labels.get(key, key)
                messagebox.showerror(
                    "入力値エラー",
                    f"パラメータ「{label}」に不正な値が入力されています。\n"
                    "数値（整数または小数）を入力してください。"
                )
                return None
        return params

    def set_params(self, params: dict):
        for k, v in params.items():
            if k in self.vars:
                try:
                    self.vars[k].set(v)
                except Exception:
                    pass
