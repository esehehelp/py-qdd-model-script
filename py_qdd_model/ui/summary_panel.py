import tkinter as tk
from tkinter import ttk
from typing import Dict

class SummaryPanel(ttk.Labelframe):
    def __init__(self, master, layout, *args, **kwargs):
        super().__init__(master, *args, text='サマリー', **kwargs)
        self.layout = layout
        self.vars: Dict[str, tk.StringVar] = {}
        self._build()

    def _build(self):
        row = 0
        for section, items in self.layout.items():
            ttk.Label(self, text=section, font=('TkDefaultFont', 9, 'bold')).grid(row=row, columnspan=2, sticky='w', pady=(5,2))
            row += 1
            for display, key in items:
                is_sub = display.startswith('└')
                text = display.lstrip('└ ')
                ttk.Label(self, text=text+':').grid(row=row, column=0, sticky='w', padx=(20 if is_sub else 5))
                var = tk.StringVar(value='-')
                ttk.Label(self, textvariable=var).grid(row=row, column=1, sticky='w')
                self.vars[key] = var
                row += 1

    def get_values(self):
        return {k: v.get() for k, v in self.vars.items()}

    def update(self, data: dict):
        for k, v in data.items():
            if k in self.vars:
                self.vars[k].set(v)
