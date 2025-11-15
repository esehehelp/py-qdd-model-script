import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
from ..i18n.translator import t

class ParameterPanel(ttk.Labelframe):
    def __init__(self, master, param_defs: Dict, *args, **kwargs):
        super().__init__(master, *args, text=t("ParameterPanel.TITLE"), **kwargs)
        self.param_defs = param_defs
        self.vars: Dict[str, Dict[str, tk.Variable]] = {}
        self._build()

        # Create a flat map from schema key to tk.Variable for easy access
        self.key_to_var_map: Dict[str, tk.Variable] = {}
        for group_key, fields in self.vars.items():
            for field_key, var in fields.items():
                self.key_to_var_map[field_key] = var

    def _build(self):
        """Builds the UI by creating nested labelframes and widgets based on param_defs."""
        container = ttk.Frame(self)
        container.pack(fill='x', expand=True)

        is_first_group = True
        for group_key, fields in self.param_defs.items():
            is_schema_key = group_key in ["electrical", "winding", "magnets", "geometry", "thermal", "driver", "gear", "simulation"]
            
            frame_label = group_key if not is_schema_key else t(f"Layout.PARAM_DEFS.groups.{group_key}", default=group_key.capitalize())
            
            if is_first_group:
                frame = ttk.Frame(container)
                is_first_group = False
            else:
                frame = ttk.LabelFrame(container, text=frame_label, padding=5)
            frame.pack(fill='x', padx=5, pady=5)

            self.vars[group_key] = {}
            
            items = list(fields.items())
            for i, (key, value_tuple) in enumerate(items):
                r = i // 2
                c = (i % 2) * 2
                
                label_text, default_val, *rest = value_tuple
                
                ttk.Label(frame, text=label_text).grid(row=r, column=c, sticky='w', padx=5, pady=2)
                
                var: tk.Variable
                widget: ttk.Widget
                
                if isinstance(default_val, bool):
                    var = tk.BooleanVar(value=default_val)
                    widget = ttk.Checkbutton(frame, variable=var)
                elif rest and isinstance(rest[0], list):
                    var = tk.StringVar(value=default_val)
                    widget = ttk.Combobox(frame, textvariable=var, values=rest[0], width=10, state='readonly')
                elif isinstance(default_val, str):
                    var = tk.StringVar(value=default_val)
                    widget = ttk.Entry(frame, textvariable=var, width=20)
                else: # float or int
                    var = tk.DoubleVar(value=default_val)
                    widget = ttk.Entry(frame, textvariable=var, width=12)
                    
                widget.grid(row=r, column=c + 1, sticky='e', padx=5, pady=2)
                self.vars[group_key][key] = var

    def get_params(self) -> Dict[str, Any]:
        """Recursively gets parameters from the UI and returns them in a nested dictionary."""
        params: Dict[str, Any] = {}
        
        param_labels: Dict[str, str] = {}
        for group_data in self.param_defs.values():
            for key, value_tuple in group_data.items():
                param_labels[key] = value_tuple[0]

        for group_key, field_vars in self.vars.items():
            is_schema_key = group_key in ["electrical", "winding", "magnets", "geometry", "thermal", "driver", "gear", "simulation"]
            
            if is_schema_key:
                if group_key not in params:
                    params[group_key] = {}
                target_dict = params[group_key]
            else:
                target_dict = params

            for key, var in field_vars.items():
                try:
                    target_dict[key] = var.get()
                except tk.TclError:
                    label = param_labels.get(key, key)
                    messagebox.showerror(
                        t("Dialog.Title.INPUT_ERROR"),
                        t("Dialog.Message.INVALID_NUMERIC_VALUE").format(label)
                    )
                    return {}
        return params

    def set_params(self, params: Dict[str, Any]):
        """Sets UI parameters from a nested dictionary based on schema keys."""
        for key, value in params.items():
            if isinstance(value, dict):
                # Nested group (e.g., "electrical")
                for sub_key, sub_value in value.items():
                    if sub_key in self.key_to_var_map:
                        try:
                            self.key_to_var_map[sub_key].set(sub_value)
                        except tk.TclError:
                            print(f"Warning: Could not set '{sub_key}' to '{sub_value}'. Type mismatch?")
            else:
                # Top-level parameter (e.g., "name")
                if key in self.key_to_var_map:
                    try:
                        self.key_to_var_map[key].set(value)
                    except tk.TclError:
                        print(f"Warning: Could not set '{key}' to '{value}'. Type mismatch?")