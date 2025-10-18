import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from ..schema import MotorParams
from ..models.motor_model import MotorModel
from ..ui.parameter_panel import ParameterPanel
from ..ui.summary_panel import SummaryPanel
from ..ui.plot_view import PlotView
from ..utils.io import save_json, load_json

Z_AXIS_MAP = {
    '総合効率 [%]': 'efficiency',
    'トルク [Nm]': 'torque',
    '出力パワー [W]': 'output_power',
    '必要電圧 [V]': 'voltage',
    '全損失 [W]': 'total_loss'
}

SUMMARY_LAYOUT = {
    'ピーク性能': [
        ('最大総合効率', 'max_eff_val'),
        ('└ 回転数/電流/トルク', 'max_eff_point'),
        ('最大出力パワー', 'max_power_val'),
        ('└ 回転数/電流/トルク', 'max_power_point'),
        ('最大トルク', 'max_torque_val'),
        ('└ 回転数/電流', 'max_torque_point')
    ],
    '定格動作時 (連続電流)': [
        ('最大効率', 'rated_eff_val'),
        ('└ 回転数/トルク/パワー', 'rated_point')
    ]
}

class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('QDDモーター特性モデリングツール')
        self.pack(fill='both', expand=True)

        self.param_defs = {
            'モーター基本特性': {
                'kv': ('KV値 [rpm/V]', 100.0),
                'phase_resistance': ('一相あたり抵抗 (25℃) [Ohm]', 0.1),
                'phase_inductance': ('一相あたりインダクタンス [H]', 0.0001),
                'pole_pairs': ('極対数', 7),
                'wiring_type': ('配線方式', 'star', ['star','delta']),
                'continuous_current': ('連続電流 [A]', 10.0),
                'peak_current': ('ピーク電流 [A]', 30.0)
            },
            '熱モデル': {
                'ambient_temperature': ('周囲温度 [°C]', 25.0),
                'thermal_resistance': ('モーター熱抵抗 [°C/W]', 2.0)
            },
            '鉄損モデル': {
                'hysteresis_coeff': ('ヒステリシス係数 [W/rpm]', 0.001),
                'eddy_current_coeff': ('渦電流係数 [W/rpm^2]', 1e-7)
            },
            'ドライバ損失モデル': {
                'driver_on_resistance': ('ドライバON抵抗 [Ohm]', 0.005),
                'driver_fixed_loss': ('ドライバ固定損失 [W]', 2.0)
            },
            'ギア損失モデル': {
                'gear_ratio': ('減速比', 9.0),
                'gear_efficiency': ('ギア効率', 0.95)
            },
            '動作条件': {
                'bus_voltage': ('バス電圧 [V]', 48.0)
            }
        }

        left = ttk.Frame(self, padding=10)
        left.pack(side='left', fill='y')

        self.param_panel = ParameterPanel(left, self.param_defs)
        self.param_panel.pack(fill='x')

        self.summary_panel = SummaryPanel(left, SUMMARY_LAYOUT)
        self.summary_panel.pack(fill='x', pady=8)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=8, fill='x')
        ttk.Button(btn_frame, text='計算＆プロット', command=self.run_analysis).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='プリセット読込', command=self.load_preset).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='プリセット保存', command=self.save_preset).pack(side='left', padx=4)

        # --- 出力機能 ---
        out_frame = ttk.Frame(left)
        out_frame.pack(pady=8, fill='x')
        ttk.Button(out_frame, text='サマリー保存', command=self.save_summary).pack(side='left', padx=4)
        ttk.Button(out_frame, text='PNG保存', command=self.save_plot).pack(side='left', padx=4)

        self.plot_view = PlotView(self)

        # Z軸選択
        ttk.Label(left, text='グラフZ軸').pack()
        self.z_var = tk.StringVar(value='総合効率 [%]')
        ttk.Combobox(left, textvariable=self.z_var, values=list(Z_AXIS_MAP.keys()), width=20).pack()

        self.results = None

    def _get_params_validated(self):
        raw = self.param_panel.get_params()
        try:
            params = MotorParams(**raw)
            return params
        except Exception as e:
            messagebox.showerror('入力エラー', f'パラメータ検証に失敗しました:\n{e}')
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
            motor_rpm_unloaded = params.bus_voltage / ke_line * (60 / (2 * np.pi))
            theoretical_max_rpm = motor_rpm_unloaded / params.gear_ratio
        else:
            theoretical_max_rpm = 5000

        current_range = np.linspace(0.1, params.peak_current, 50)
        rpm_range = np.linspace(0.1, theoretical_max_rpm * 1.1, 50)
        I, RPM = np.meshgrid(current_range, rpm_range)

        results = model.analyze(I, RPM)
        self.results = results

        # サマリー作成
        valid_mask = results['voltage'] <= params.bus_voltage

        def get_summary(key):
            if not np.any(valid_mask):
                return None, None
            data = np.where(valid_mask, results[key], np.nan)
            if not np.any(~np.isnan(data)):
                return None, None
            idx = np.nanargmax(data)
            coords = np.unravel_index(idx, data.shape)
            val = data[coords]
            return val, coords

        max_eff, eff_coords = get_summary('efficiency')
        if max_eff is not None:
            self.summary_panel.update({'max_eff_val': f'{max_eff*100:.1f} %',
                                       'max_eff_point': f"{results['rpm'][eff_coords]:.0f} RPM / {results['current'][eff_coords]:.1f} A / {results['torque'][eff_coords]:.2f} Nm"})

        max_power, power_coords = get_summary('output_power')
        if max_power is not None:
            self.summary_panel.update({'max_power_val': f'{max_power:.1f} W',
                                       'max_power_point': f"{results['rpm'][power_coords]:.0f} RPM / {results['current'][power_coords]:.1f} A / {results['torque'][power_coords]:.2f} Nm"})

        max_torque, torque_coords = get_summary('torque')
        if max_torque is not None:
            self.summary_panel.update({'max_torque_val': f'{max_torque:.2f} Nm',
                                       'max_torque_point': f"{results['rpm'][torque_coords]:.0f} RPM / {results['current'][torque_coords]:.1f} A"})

        cont_idx = np.argmin(np.abs(current_range - params.continuous_current))
        rated_mask = valid_mask[:, cont_idx]
        rated_eff = np.where(rated_mask, results['efficiency'][:, cont_idx], np.nan)
        if np.any(~np.isnan(rated_eff)):
            rated_idx = np.nanargmax(rated_eff)
            self.summary_panel.update({'rated_eff_val': f'{rated_eff[rated_idx]*100:.1f} %',
                                       'rated_point': f"{RPM[rated_idx, cont_idx]:.0f} RPM / {results['torque'][rated_idx, cont_idx]:.2f} Nm / {results['output_power'][rated_idx, cont_idx]:.1f} W"})

        # Plot
        zkey = Z_AXIS_MAP[self.z_var.get()]
        Z = results[zkey].copy()
        if zkey == 'efficiency':
            Z *= 100
        Z[~valid_mask] = np.nan

        self.plot_view.plot(I, RPM, Z, '電流 [A]', '回転数 [RPM]', self.z_var.get(), f'QDDモーター特性マップ: {self.z_var.get()}')

    def save_preset(self):
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(defaultextension='.json')
        if not fp:
            return
        raw = self.param_panel.get_params()
        save_json(fp, raw)
        messagebox.showinfo('保存完了', f'プリセットを {fp} に保存しました。')

    def load_preset(self):
        from tkinter.filedialog import askopenfilename
        fp = askopenfilename()
        if not fp:
            return
        try:
            data = load_json(fp)
            self.param_panel.set_params(data)
            messagebox.showinfo('読込完了', 'プリセットを読み込みました。')
        except Exception as e:
            messagebox.showerror('読込エラー', f'{e}')

    def save_plot(self):
        if self.results is None:
            messagebox.showwarning('警告', '先に「計算＆プロット」を実行してください。')
            return
        from tkinter.filedialog import asksaveasfilename
        fp = asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG Image', '*.png'), ('All files', '*.*')]
        )
        if not fp:
            return
        try:
            self.plot_view.save_png(fp)
            messagebox.showinfo('保存完了', f'グラフを {fp} に保存しました。')
        except Exception as e:
            messagebox.showerror('保存エラー', f'ファイルの保存に失敗しました:\n{e}')

    def save_summary(self):
        if self.results is None:
            messagebox.showwarning('警告', '先に「計算＆プロット」を実行してください。')
            return
        from tkinter.filedialog import asksaveasfilename
        from ..utils.io import save_text
        fp = asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text File', '*.txt'), ('All files', '*.*')]
        )
        if not fp:
            return

        summary_text = "QDDモーター性能サマリー\n"
        summary_text += "="*40 + "\n"

        summary_data = self.summary_panel.get_values()

        for section, items in SUMMARY_LAYOUT.items():
            summary_text += f"\n{section}\n"
            summary_text += "-"*len(section)*2 + "\n"
            for display, key in items:
                label = display.lstrip('└ ')
                value = summary_data.get(key, '-')
                summary_text += f"{label:>22s}: {value}\n"

        summary_text += "\n" + "="*40 + "\n"
        summary_text += "使用したパラメータ:\n\n"
        params = self.param_panel.get_params()
        param_defs_flat = {k: v for section in self.param_defs.values() for k, v in section.items()}

        for key, value in params.items():
            label = param_defs_flat.get(key, [key])[0]
            summary_text += f"- {label}: {value}\n"

        try:
            save_text(fp, summary_text)
            messagebox.showinfo('保存完了', f'サマリーを {fp} に保存しました。')
        except Exception as e:
            messagebox.showerror('保存エラー', f'ファイルの保存に失敗しました:\n{e}')
