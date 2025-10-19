# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
import json
import pathlib
from pydantic import ValidationError

from ..schema import MotorParams
from ..models.motor_model import MotorModel
from ..ui.parameter_panel import ParameterPanel
from ..ui.summary_panel import SummaryPanel
from ..ui.plot_view import PlotView
from ..utils.io import save_json, load_json, save_text
from ..analysis.results_analyzer import ResultsAnalyzer
from ..exceptions import FileOperationError
from ..models import winding_model as winding_calculator
from . import constants as C_UI
from .. import constants as C_MODEL
from ..utils.config import settings

class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title(C_UI.WINDOW_TITLE)
        self.master.geometry(settings["window"]["initial_size"])
        self.pack(fill='both', expand=True)

        self.param_defs = C_UI.Layout.PARAM_DEFS

        left = ttk.Frame(self, padding=settings["layout"]["main_padding"])
        left.pack(side='left', fill='y')

        self.param_panel = ParameterPanel(left, self.param_defs)
        self.param_panel.pack(fill='x')

        self.summary_panel = SummaryPanel(left, C_UI.Layout.SUMMARY_LAYOUT)
        self.summary_panel.pack(fill='x', pady=settings["layout"]["widget_pady"])

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=settings["layout"]["widget_pady"], fill='x')
        ttk.Button(btn_frame, text=C_UI.Buttons.RUN, command=self.run_analysis).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(btn_frame, text=C_UI.Buttons.LOAD_PRESET, command=self.load_preset).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(btn_frame, text=C_UI.Buttons.SAVE_PRESET, command=self.save_preset).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(btn_frame, text=C_UI.Buttons.WINDING_CALC, command=self.run_winding_calculation).pack(side='left', padx=settings["layout"]["button_padx"])

        # --- 出力機能 ---
        out_frame = ttk.Frame(left)
        out_frame.pack(pady=settings["layout"]["widget_pady"], fill='x')
        ttk.Button(out_frame, text=C_UI.Buttons.SAVE_SUMMARY, command=self.save_summary).pack(side='left', padx=settings["layout"]["button_padx"])
        ttk.Button(out_frame, text=C_UI.Buttons.SAVE_PLOT, command=self.save_plot).pack(side='left', padx=settings["layout"]["button_padx"])

        self.plot_view = PlotView(self)

        # Z軸選択
        ttk.Label(left, text=C_UI.Plot.Z_AXIS_LABEL).pack()
        self.z_var = tk.StringVar(value=list(C_UI.Plot.Z_AXIS_MAP.keys())[0])
        ttk.Combobox(left, textvariable=self.z_var, values=list(C_UI.Plot.Z_AXIS_MAP.keys()), width=settings["layout"]["combobox_width"]).pack()

        self.results = None

    def _get_params_validated(self):
        raw = self.param_panel.get_params()
        if raw is None:
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
        
        model = MotorModel(params)

        if params.wiring_type == 'star':
            ke_line = model.ke * np.sqrt(3)
        else:
            ke_line = model.ke

        if ke_line > 0:
            motor_rpm_unloaded = params.bus_voltage / ke_line * C_MODEL.PhysicsConstants.RAD_PER_SEC_TO_RPM
            theoretical_max_rpm = motor_rpm_unloaded / params.gear_ratio
        else:
            theoretical_max_rpm = C_MODEL.ModelDefaults.FALLBACK_MAX_RPM

        current_range = np.linspace(0.1, params.peak_current, settings["analysis"]["grid_points"])
        rpm_range = np.linspace(0.1, theoretical_max_rpm * settings["analysis"]["rpm_safety_margin"], settings["analysis"]["grid_points"])
        I, RPM = np.meshgrid(current_range, rpm_range)

        results = model.analyze(I, RPM)
        self.results = results

        # サマリー作成とUI更新
        analyzer = ResultsAnalyzer(params, results, current_range)
        summary = analyzer.calculate_summary()
        self.summary_panel.update(summary)

        # Plot
        z_selection = self.z_var.get()
        zkey = C_UI.Plot.Z_AXIS_MAP[z_selection]
        Z = results[zkey].copy()
        if zkey == 'efficiency':
            Z *= 100

        valid_mask = results['voltage'] <= params.bus_voltage
        Z[~valid_mask] = np.nan

        self.plot_view.plot(I, RPM, Z, C_UI.Plot.X_AXIS_LABEL, C_UI.Plot.Y_AXIS_LABEL, z_selection, C_UI.Plot.PLOT_TITLE.format(z_selection))

        self.results = results
        self.last_result = results
        self.model = model

    def run_winding_calculation(self):
        target_params = self.param_panel.get_params()
        if target_params is None or not all(k in target_params for k in ["kv", "peak_current"]):
            messagebox.showerror(C_UI.Dialog.Title.ERROR, C_UI.Dialog.Message.WINDING_CALC_MISSING_PARAMS)
            return

        density = simpledialog.askfloat(C_UI.Dialog.Title.WINDING_CALC_INPUT, C_UI.Dialog.Message.WINDING_CALC_DENSITY_PROMPT, minvalue=1.0, maxvalue=50.0, initialvalue=8.0)
        if density is None:
            return

        use_custom_ref = messagebox.askyesno(C_UI.Dialog.Title.WINDING_CALC_REF, C_UI.Dialog.Message.WINDING_CALC_USE_CUSTOM_REF)
        
        reference_params = None
        ref_name = ""
        if use_custom_ref:
            from tkinter.filedialog import askopenfilename
            fp = askopenfilename(filetypes=[C_UI.FileDialog.JSON])
            if not fp:
                return
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    reference_params = json.load(f)
                ref_name = pathlib.Path(fp).name
            except (IOError, json.JSONDecodeError) as e:
                messagebox.showerror(C_UI.Dialog.Title.ERROR, C_UI.Dialog.Message.WINDING_CALC_LOAD_REF_ERROR.format(e))
                return
        else:
            reference_params = winding_calculator.BUILTIN_PROFILES["medium"]
            ref_name = "built-in 'medium' profile"

        try:
            results = winding_calculator.estimate_new_winding(target_params, reference_params, density)
        except KeyError as e:
            messagebox.showerror(C_UI.Dialog.Title.ERROR, C_UI.Dialog.Message.WINDING_CALC_KEY_ERROR.format(e))
            return

        self.param_panel.set_params({
            "phase_resistance": results["resistance"],
            "phase_inductance": results["inductance"]
        })

        result_message = C_UI.Dialog.Message.WINDING_CALC_COMPLETE.format(
            ref_name,
            results['resistance'],
            results['inductance'],
            results['diameter_mm'],
            results['length']
        )
        messagebox.showinfo(C_UI.Dialog.Title.WINDING_CALC_COMPLETE, result_message)

    def save_preset(self):
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.json',
            filetypes=[C_UI.FileDialog.JSON, C_UI.FileDialog.ALL]
        )
        if not fp:
            return
        
        raw = self.param_panel.get_params()
        if raw is None:
            return
        
        try:
            save_json(fp, raw)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.PRESET_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))

    def load_preset(self):
        from tkinter.filedialog import askopenfilename
        fp = askopenfilename(
            filetypes=[C_UI.FileDialog.JSON, C_UI.FileDialog.ALL]
        )
        if not fp:
            return
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
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.png',
            filetypes=[C_UI.FileDialog.PNG, C_UI.FileDialog.ALL]
        )
        if not fp:
            return
        try:
            self.plot_view.save_png(fp)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.PLOT_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))

    def save_summary(self):
        if self.results is None:
            messagebox.showwarning(C_UI.Dialog.Title.WARNING, C_UI.Dialog.Message.RUN_FIRST)
            return
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.txt',
            filetypes=[C_UI.FileDialog.TXT, C_UI.FileDialog.ALL]
        )
        if not fp:
            return

        summary_text = f"{C_UI.SummaryReport.TITLE}\n"
        summary_text += "="*40 + "\n"

        summary_data = self.summary_panel.get_values()

        for section, items in C_UI.Layout.SUMMARY_LAYOUT.items():
            summary_text += f"\n{section}\n"
            summary_text += "-"*len(section)*2 + "\n"
            for display, key in items:
                label = display.lstrip('└ ')
                value = summary_data.get(key, '-')
                summary_text += f"{label:>22s}: {value}\n"

        summary_text += "\n" + "="*40 + "\n"
        summary_text += f"{C_UI.SummaryReport.PARAMS_HEADER}\n\n"
        params = self.param_panel.get_params()
        param_defs_flat = {k: v for section in self.param_defs.values() for k, v in section.items()}

        for key, value in params.items():
            label = param_defs_flat.get(key, [key])[0]
            summary_text += f"- {label}: {value}\n"

        try:
            save_text(fp, summary_text)
            messagebox.showinfo(C_UI.Dialog.Title.SAVE_COMPLETE, C_UI.Dialog.Message.SUMMARY_SAVED.format(fp))
        except FileOperationError as e:
            messagebox.showerror(C_UI.Dialog.Title.SAVE_ERROR, str(e))