# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pathlib
from pydantic import ValidationError
from typing import Dict, Any
from tkinter.filedialog import askdirectory, asksaveasfilename, askopenfilename
import multiprocessing

from ..schema import MotorParams
from ..models.motor_model import MotorModel
from ..ui.parameter_panel import ParameterPanel
from ..ui.summary_panel import SummaryPanel
from ..ui.plot_view import PlotView
from ..utils.io import save_json, load_json, save_text
from ..utils import csv_exporter
from ..analysis.results_analyzer import ResultsAnalyzer
from ..analysis.parallel_analyzer import run_parallel_analysis
from ..exceptions import FileOperationError
from ..three_d import model_generator
from . import constants as C_UI
from .. import constants as C_MODEL
from ..utils.config import settings
from ..i18n.translator import t

class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title(C_UI.WINDOW_TITLE)
        self.master.geometry(settings["window"]["initial_size"])
        self.pack(fill='both', expand=True)

        self.param_defs = C_UI.Layout.get_param_defs()

        left = ttk.Frame(self, padding=settings["layout"]["main_padding"])
        left.pack(side='left', fill='y', anchor='n')

        # Create a scrollable frame for the parameter panel
        param_container = ttk.Frame(left)
        param_container.pack(fill="both", expand=True)

        param_canvas = tk.Canvas(param_container)
        param_v_scrollbar = ttk.Scrollbar(param_container, orient="vertical", command=param_canvas.yview)
        param_h_scrollbar = ttk.Scrollbar(param_container, orient="horizontal", command=param_canvas.xview)
        param_scrollable_frame = ttk.Frame(param_canvas)

        param_scrollable_frame.bind(
            "<Configure>",
            lambda e: param_canvas.configure(
                scrollregion=param_canvas.bbox("all")
            )
        )

        param_canvas.create_window((0, 0), window=param_scrollable_frame, anchor="nw")
        param_canvas.configure(yscrollcommand=param_v_scrollbar.set, xscrollcommand=param_h_scrollbar.set)

        self.param_panel = ParameterPanel(param_scrollable_frame, self.param_defs)
        self.param_panel.pack(fill='x', expand=True)

        param_v_scrollbar.pack(side="left", fill="y")
        param_h_scrollbar.pack(side="bottom", fill="x")
        param_canvas.pack(side="left", fill="both", expand=True)

        self.summary_panel = SummaryPanel(left, C_UI.Layout.SUMMARY_LAYOUT)
        self.summary_panel.pack(fill='x', pady=settings["layout"]["widget_pady"])

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=settings["layout"]["widget_pady"], fill='x')
        ttk.Button(btn_frame, text=C_UI.Buttons.RUN, command=self.run_analysis).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(btn_frame, text=C_UI.Buttons.LOAD_PRESET, command=self.load_preset).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(btn_frame, text=C_UI.Buttons.SAVE_PRESET, command=self.save_preset).pack(side='left', padx=settings["layout"]["button_padx"])

        out_frame = ttk.Frame(left)
        out_frame.pack(pady=settings["layout"]["widget_pady"], fill='x')
        ttk.Button(out_frame, text=C_UI.Buttons.SAVE_SUMMARY, command=self.save_summary).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(out_frame, text=C_UI.Buttons.SAVE_PLOT, command=self.save_plot).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(out_frame, text=C_UI.Buttons.GENERATE_3D_MODEL, command=self.generate_3d_model).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(out_frame, text=C_UI.Buttons.EXPORT_CSV_FUSION, command=self.export_csv_for_fusion).pack(side='left', padx=settings["layout"]["button_padx"])

        self.plot_view = PlotView(self)

        z_axis_frame = ttk.Frame(left)
        z_axis_frame.pack(pady=settings["layout"]["widget_pady"], fill='x')
        ttk.Label(z_axis_frame, text=C_UI.Plot.Z_AXIS_LABEL).pack(side='left')
        self.z_var = tk.StringVar(value=list(C_UI.Plot.Z_AXIS_MAP.keys())[0])
        z_combo = ttk.Combobox(z_axis_frame, textvariable=self.z_var, values=list(C_UI.Plot.Z_AXIS_MAP.keys()), width=settings["layout"]["combobox_width"], state='readonly')
        z_combo.pack(side='left', padx=5)
        z_combo.bind('<<ComboboxSelected>>', self.on_z_axis_change)

        self.results = None

        self.status_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.status_var, anchor='w').pack(side='bottom', fill='x', pady=5)

    def _get_params_validated(self):
        raw = self.param_panel.get_params()
        if not raw:
            return None
        
        try:
            params = MotorParams(**raw)
            return params
        except ValidationError as e:
            messagebox.showerror(C_UI.Dialog.Title.INPUT_ERROR, C_UI.Dialog.Message.PARAMS_VALIDATION_FAILED.format(e))
            return None

    def run_analysis(self):
        params = self._get_params_validated()
        if params is None:
            return

        temp_model = MotorModel(params)
        if params.winding.wiring_type == 'star':
            ke_line = temp_model.ke * np.sqrt(3)
        else:
            ke_line = temp_model.ke

        if ke_line > 0:
            motor_rpm_unloaded = params.simulation.bus_voltage / ke_line * C_MODEL.PhysicsConstants.RAD_PER_SEC_TO_RPM
            theoretical_max_rpm = motor_rpm_unloaded / params.gear.gear_ratio
        else:
            theoretical_max_rpm = C_MODEL.ModelDefaults.FALLBACK_MAX_RPM

        current_range = np.linspace(0.1, params.winding.peak_current, settings["analysis"]["grid_points"])
        rpm_range = np.linspace(0.1, theoretical_max_rpm * settings["analysis"]["rpm_safety_margin"], settings["analysis"]["grid_points"])
        
        self.status_var.set(t("Dialog.Message.STATUS_CALCULATING"))
        self.master.update_idletasks()

        results = run_parallel_analysis(params.model_copy(deep=True), current_range, rpm_range)
        self.results = results

        analyzer = ResultsAnalyzer(params, results, current_range)
        summary = analyzer.calculate_summary()
        self.summary_panel.update(summary)

        self.status_var.set(t("Dialog.Message.STATUS_PLOTTING"))
        self.master.update_idletasks()

        self.plot_current_view()

        self.status_var.set("")
        self.master.update_idletasks()

    def on_z_axis_change(self, event=None):
        self.plot_current_view()

    def plot_current_view(self):
        if self.results is None:
            return

        params = self._get_params_validated()
        if params is None:
            return

        z_selection = self.z_var.get()
        zkey = C_UI.Plot.Z_AXIS_MAP[z_selection]
        Z = self.results[zkey].copy()
        if zkey == 'efficiency':
            Z *= 100

        valid_mask = self.results['voltage'] <= params.simulation.bus_voltage
        Z[~valid_mask] = np.nan
        
        current_range = np.linspace(0.1, params.winding.peak_current, settings["analysis"]["grid_points"])
        
        temp_model = MotorModel(params)
        if params.winding.wiring_type == 'star':
            ke_line = temp_model.ke * np.sqrt(3)
        else:
            ke_line = temp_model.ke
        if ke_line > 0:
            motor_rpm_unloaded = params.simulation.bus_voltage / ke_line * C_MODEL.PhysicsConstants.RAD_PER_SEC_TO_RPM
            theoretical_max_rpm = motor_rpm_unloaded / params.gear.gear_ratio
        else:
            theoretical_max_rpm = C_MODEL.ModelDefaults.FALLBACK_MAX_RPM
        rpm_range = np.linspace(0.1, theoretical_max_rpm * settings["analysis"]["rpm_safety_margin"], settings["analysis"]["grid_points"])
        I, RPM = np.meshgrid(current_range, rpm_range)

        self.plot_view.plot(I, RPM, Z, C_UI.Plot.X_AXIS_LABEL, C_UI.Plot.Y_AXIS_LABEL, z_selection, C_UI.Plot.PLOT_TITLE.format(z_selection))

    def generate_3d_model(self):
        params = self._get_params_validated()
        if params is None:
            return

        output_dir_str = askdirectory(title="Select Output Directory for 3D Model")
        if not output_dir_str:
            return
        output_dir = pathlib.Path(output_dir_str)

        try:
            process = multiprocessing.Process(
                target=model_generator.generate_motor_model,
                args=(params, output_dir)
            )
            process.start()
            
            messagebox.showinfo(
                "3D Model Generation",
                f"3D model generation for '{params.name}' has started in the background.\n"
                f"The file will be saved in: {output_dir}"
            )
        except Exception as e:
            messagebox.showerror("3D Model Generation Error", f"Failed to start the generation process: {e}")

    def export_csv_for_fusion(self):
        params = self._get_params_validated()
        if params is None:
            return

        try:
            csv_data = csv_exporter.export_params_to_fusion_csv(params, self.param_defs)
        except Exception as e:
            messagebox.showerror("CSV Export Error", f"Failed to generate CSV data: {e}")
            return

        fp = asksaveasfilename(
            defaultextension='.csv',
            filetypes=[("CSV files", '*.csv'), ("All files", '*.*')],
            initialfile=f"{params.name.replace(' ', '_')}_fusion_params.csv"
        )
        if not fp:
            return

        try:
            with open(fp, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_data)
            messagebox.showinfo("CSV Export Complete", f"Parameters saved to {fp}")
        except IOError as e:
            messagebox.showerror("CSV Export Error", f"Failed to save CSV file: {e}")

    def save_preset(self):
        fp = asksaveasfilename(defaultextension='.json', filetypes=[C_UI.FileDialog.JSON, C_UI.FileDialog.ALL])
        if not fp: return
        
        raw = self.param_panel.get_params()
        if not raw: return
        
        try:
            save_json(fp, raw)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.PRESET_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))

    def load_preset(self):
        fp = askopenfilename(filetypes=[C_UI.FileDialog.JSON, C_UI.FileDialog.ALL])
        if not fp: return
        try:
            data = load_json(fp)
            self.param_panel.set_params(data)
            messagebox.showinfo(C_UI.Dialog.Title.LOAD_COMPLETE, C_UI.Dialog.Message.PRESET_LOADED)
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.LOAD_ERROR, C_UI.Dialog.Message.PRESET_LOAD_FAILED.format(e))

    def save_plot(self):
        if self.results is None:
            messagebox.showwarning(C_UI.Dialog.Title.WARNING, C_UI.Dialog.Message.RUN_FIRST)
            return
        fp = asksaveasfilename(defaultextension='.png', filetypes=[C_UI.FileDialog.PNG, C_UI.FileDialog.ALL])
        if not fp: return
        try:
            self.plot_view.save_png(fp)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.PLOT_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))

    def _format_params_recursively(self, params_dict: Dict[str, Any], param_defs: Dict, level: int = 0) -> str:
        """Helper function to recursively format nested parameter dictionaries."""
        text = ""
        indent = "  " * level
        
        flat_defs = {}
        for group_key, group_fields in param_defs.items():
            is_schema_key = group_key in ["electrical", "winding", "magnets", "geometry", "thermal", "driver", "gear", "simulation"]
            if is_schema_key:
                 for key, T in group_fields.items():
                     flat_defs[key] = T[0]
            else: # Top-level group
                for key, T in group_fields.items():
                    flat_defs[key] = T[0]

        for key, value in params_dict.items():
            if isinstance(value, dict):
                group_label = t(f"Layout.PARAM_DEFS.groups.{key}", default=key.capitalize())
                text += f"\n{indent}[{group_label}]\n"
                text += self._format_params_recursively(value, param_defs, level + 1)
            else:
                label = flat_defs.get(key, key)
                text += f"{indent}- {label}: {value}\n"
        return text

    def save_summary(self):
        if self.results is None:
            messagebox.showwarning(C_UI.Dialog.Title.WARNING, C_UI.Dialog.Message.RUN_FIRST)
            return
        fp = asksaveasfilename(defaultextension='.txt', filetypes=[C_UI.FileDialog.TXT, C_UI.FileDialog.ALL])
        if not fp: return

        summary_text = f"{C_UI.SummaryReport.TITLE}\n{'='*40}\n"
        summary_data = self.summary_panel.get_values()

        for section, items in C_UI.Layout.SUMMARY_LAYOUT.items():
            summary_text += f"\n{section}\n{'-'*len(section)*2}\n"
            for display, key in items:
                label = display.lstrip('└ ')
                value = summary_data.get(key, '-')
                summary_text += f"{label:>22s}: {value}\n"

        summary_text += f"\n{'='*40}\n{C_UI.SummaryReport.PARAMS_HEADER}\n"
        params = self.param_panel.get_params()
        summary_text += self._format_params_recursively(params, self.param_defs)

        try:
            save_text(fp, summary_text)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.SUMMARY_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))