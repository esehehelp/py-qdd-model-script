# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from ..schema import MotorParams
from ..models.motor_model import MotorModel
from ..ui.parameter_panel import ParameterPanel
from ..ui.summary_panel import SummaryPanel
from ..ui.plot_view import PlotView
from ..utils.io import save_json, load_json, save_text
from ..analysis.results_analyzer import ResultsAnalyzer
from . import constants as C_UI
from .. import constants as C_MODEL

class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title(C_UI.WINDOW_TITLE)
        self.pack(fill='both', expand=True)

        self.param_defs = C_UI.PARAM_DEFS

        left = ttk.Frame(self, padding=10)
        left.pack(side='left', fill='y')

        self.param_panel = ParameterPanel(left, self.param_defs)
        self.param_panel.pack(fill='x')

        self.summary_panel = SummaryPanel(left, C_UI.SUMMARY_LAYOUT)
        self.summary_panel.pack(fill='x', pady=8)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=8, fill='x')
        ttk.Button(btn_frame, text=C_UI.RUN_BUTTON, command=self.run_analysis).pack(side='left', padx=4)
        ttk.Button(btn_frame, text=C_UI.LOAD_PRESET_BUTTON, command=self.load_preset).pack(side='left', padx=4)
        ttk.Button(btn_frame, text=C_UI.SAVE_PRESET_BUTTON, command=self.save_preset).pack(side='left', padx=4)

        # --- 出力機能 ---
        out_frame = ttk.Frame(left)
        out_frame.pack(pady=8, fill='x')
        ttk.Button(out_frame, text=C_UI.SAVE_SUMMARY_BUTTON, command=self.save_summary).pack(side='left', padx=4)
        ttk.Button(out_frame, text=C_UI.SAVE_PLOT_BUTTON, command=self.save_plot).pack(side='left', padx=4)

        self.plot_view = PlotView(self)

        # Z軸選択
        ttk.Label(left, text=C_UI.Z_AXIS_LABEL).pack()
        self.z_var = tk.StringVar(value=list(C_UI.Z_AXIS_MAP.keys())[0])
        ttk.Combobox(left, textvariable=self.z_var, values=list(C_UI.Z_AXIS_MAP.keys()), width=20).pack()

        self.results = None

    def _get_params_validated(self):
        raw = self.param_panel.get_params()
        if raw is None:
            return None
            
        try:
            params = MotorParams(**raw)
            return params
        except Exception as e:
            messagebox.showerror(C_UI.INPUT_ERROR_TITLE, C_UI.PARAMS_VALIDATION_FAILED_MSG.format(e))
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

        current_range = np.linspace(0.1, params.peak_current, C_MODEL.ModelDefaults.ANALYSIS_POINTS)
        rpm_range = np.linspace(0.1, theoretical_max_rpm * C_MODEL.ModelDefaults.RPM_SAFETY_MARGIN, C_MODEL.ModelDefaults.ANALYSIS_POINTS)
        I, RPM = np.meshgrid(current_range, rpm_range)

        results = model.analyze(I, RPM)
        self.results = results

        # サマリー作成とUI更新
        analyzer = ResultsAnalyzer(params, results, current_range)
        summary = analyzer.calculate_summary()
        self.summary_panel.update(summary)

        # Plot
        z_selection = self.z_var.get()
        zkey = C_UI.Z_AXIS_MAP[z_selection]
        Z = results[zkey].copy()
        if zkey == 'efficiency':
            Z *= 100

        valid_mask = results['voltage'] <= params.bus_voltage
        Z[~valid_mask] = np.nan

        self.plot_view.plot(I, RPM, Z, C_UI.X_AXIS_LABEL, C_UI.Y_AXIS_LABEL, z_selection, C_UI.PLOT_TITLE.format(z_selection))

        self.results = results
        self.last_result = results
        self.model = model

    def save_preset(self):
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.json',
            filetypes=[C_UI.JSON_FILE_TYPE, C_UI.ALL_FILES_TYPE]
        )
        if not fp:
            return
        
        raw = self.param_panel.get_params()
        if raw is None:
            return

        save_json(fp, raw)
        messagebox.showinfo(C_UI.SAVE_COMPLETE_TITLE, C_UI.PRESET_SAVED_MSG.format(fp))

    def load_preset(self):
        from tkinter.filedialog import askopenfilename
        fp = askopenfilename(
            filetypes=[C_UI.JSON_FILE_TYPE, C_UI.ALL_FILES_TYPE]
        )
        if not fp:
            return
        try:
            data = load_json(fp)
            self.param_panel.set_params(data)
            messagebox.showinfo(C_UI.LOAD_COMPLETE_TITLE, C_UI.PRESET_LOADED_MSG)
        except Exception as e:
            messagebox.showerror(C_UI.LOAD_ERROR_TITLE, C_UI.PRESET_LOAD_FAILED_MSG.format(e))

    def save_plot(self):
        if self.results is None:
            messagebox.showwarning(C_UI.WARNING_TITLE, C_UI.RUN_FIRST_MSG)
            return
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.png',
            filetypes=[C_UI.PNG_FILE_TYPE, C_UI.ALL_FILES_TYPE]
        )
        if not fp:
            return
        try:
            self.plot_view.save_png(fp)
            messagebox.showinfo(C_UI.SAVE_COMPLETE_TITLE, C_UI.PLOT_SAVED_MSG.format(fp))
        except Exception as e:
            messagebox.showerror(C_UI.SAVE_ERROR_TITLE, C_UI.PLOT_SAVE_FAILED_MSG.format(e))

    def save_summary(self):
        if self.results is None:
            messagebox.showwarning(C_UI.WARNING_TITLE, C_UI.RUN_FIRST_MSG)
            return
        from tkinter.filedialog import asksaveasfilename
        from ..utils.io import save_text
        fp = asksaveasfilename(
            defaultextension='.txt',
            filetypes=[C_UI.TXT_FILE_TYPE, C_UI.ALL_FILES_TYPE]
        )
        if not fp:
            return

        summary_text = f"{C_UI.SUMMARY_TITLE}\n"
        summary_text += "="*40 + "\n"

        summary_data = self.summary_panel.get_values()

        for section, items in C_UI.SUMMARY_LAYOUT.items():
            summary_text += f"\n{section}\n"
            summary_text += "-"*len(section)*2 + "\n"
            for display, key in items:
                label = display.lstrip('└ ')
                value = summary_data.get(key, '-')
                summary_text += f"{label:>22s}: {value}\n"

        summary_text += "\n" + "="*40 + "\n"
        summary_text += f"{C_UI.SUMMARY_PARAMS_HEADER}\n\n"
        params = self.param_panel.get_params()
        param_defs_flat = {k: v for section in self.param_defs.values() for k, v in section.items()}

        for key, value in params.items():
            label = param_defs_flat.get(key, [key])[0]
            summary_text += f"- {label}: {value}\n"

        try:
            save_text(fp, summary_text)
            messagebox.showinfo(C_UI.SAVE_COMPLETE_TITLE, C_UI.SUMMARY_SAVED_MSG.format(fp))
        except Exception as e:
            messagebox.showerror(C_UI.SAVE_ERROR_TITLE, C_UI.SUMMARY_SAVE_FAILED_MSG.format(e))