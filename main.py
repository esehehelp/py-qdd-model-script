import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import json
import os

plt.rcParams['font.family'] = 'Meiryo'

class CopperLossModel:
    """銅損モデル"""
    def __init__(self, params):
        self.wiring_type = params['wiring_type']

    def calculate_loss(self, current, phase_resistance):
        if self.wiring_type == 'star':
            return 3 * (current ** 2) * phase_resistance
        elif self.wiring_type == 'delta':
            return (current ** 2) * phase_resistance

class IronLossModel:
    """鉄損モデル"""
    def __init__(self, params):
        self.hysteresis_coeff = params['hysteresis_coeff']
        self.eddy_current_coeff = params['eddy_current_coeff']

    def calculate_loss(self, rpm):
        hysteresis_loss = self.hysteresis_coeff * rpm
        eddy_current_loss = self.eddy_current_coeff * (rpm ** 2)
        return hysteresis_loss + eddy_current_loss

class DriverLossModel:
    """ドライバ損失モデル"""
    def __init__(self, params):
        self.on_resistance = params['driver_on_resistance']
        self.fixed_loss = params['driver_fixed_loss']

    def calculate_loss(self, current):
        conduction_loss = (current ** 2) * self.on_resistance
        return conduction_loss + self.fixed_loss

class GearLossModel:
    """ギア損失モデル"""
    def __init__(self, params):
        self.gear_ratio = params['gear_ratio']
        self.gear_efficiency = params['gear_efficiency']

    def calculate_loss(self, motor_output_power):
        inefficient_or_no_power = (self.gear_efficiency >= 1.0) | (motor_output_power <= 0)
        gear_input_power = motor_output_power
        final_output_power = gear_input_power * self.gear_efficiency
        loss = gear_input_power - final_output_power
        loss = np.where(inefficient_or_no_power, 0, loss)
        final_output_power = np.where(inefficient_or_no_power, motor_output_power, final_output_power)
        return loss, final_output_power

class MotorModel:
    """QDDモーターのマスターモデル"""
    def __init__(self, params):
        self.params = params
        self.kt = 9.549 / params['kv']
        self.ke = self.kt  # In SI units, Kt is often equal to Ke
        self.copper_model = CopperLossModel(params)
        self.iron_model = IronLossModel(params)
        self.driver_model = DriverLossModel(params)
        self.gear_model = GearLossModel(params)
        self.COPPER_TEMP_COEFF = 0.00393  # Copper's temperature coefficient of resistance

    def analyze(self, current, rpm):
        """指定された電流とRPMでのモーター特性を解析"""
        p = self.params
        motor_rpm = rpm * p['gear_ratio']
        motor_omega_rad_s = motor_rpm * (2 * np.pi / 60)
        output_omega_rad_s = rpm * (2 * np.pi / 60)

        # --- Thermal Iteration ---
        # Initialize resistance with the value at 25°C
        phase_resistance = np.full_like(current, p['phase_resistance'])
        
        # Iterate to find steady-state temperature and resistance
        for _ in range(10): # 10 iterations are usually enough for convergence
            copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
            iron_loss = self.iron_model.calculate_loss(motor_rpm)
            driver_loss = self.driver_model.calculate_loss(current)

            # Estimate motor output power to calculate gear loss
            gross_torque_est = self.kt * current
            torque_loss_iron_est = np.divide(iron_loss, motor_omega_rad_s, out=np.zeros_like(motor_omega_rad_s), where=motor_omega_rad_s > 0)
            motor_output_torque_est = gross_torque_est - torque_loss_iron_est
            motor_output_power_est = motor_output_torque_est * motor_omega_rad_s
            gear_loss_est, _ = self.gear_model.calculate_loss(motor_output_power_est)

            total_loss = copper_loss + iron_loss + driver_loss + gear_loss_est
            
            # Calculate motor temperature
            motor_temp = p['ambient_temperature'] + total_loss * p['thermal_resistance']
            
            # Update phase resistance based on temperature
            # R = R_ref * (1 + alpha * (T - T_ref))
            phase_resistance = p['phase_resistance'] * (1 + self.COPPER_TEMP_COEFF * (motor_temp - 25))

        # --- Final Calculation with converged resistance ---
        copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
        iron_loss = self.iron_model.calculate_loss(motor_rpm)
        driver_loss = self.driver_model.calculate_loss(current)

        gross_torque = self.kt * current
        torque_loss_iron = np.divide(iron_loss, motor_omega_rad_s, out=np.zeros_like(motor_omega_rad_s), where=motor_omega_rad_s > 0)
        motor_output_torque = gross_torque - torque_loss_iron
        motor_output_torque = np.maximum(0, motor_output_torque)
        motor_output_power = motor_output_torque * motor_omega_rad_s

        gear_loss, final_output_power = self.gear_model.calculate_loss(motor_output_power)
        gearbox_output_torque = np.divide(final_output_power, output_omega_rad_s, out=np.zeros_like(output_omega_rad_s), where=output_omega_rad_s > 0)
        
        total_loss = copper_loss + iron_loss + driver_loss + gear_loss
        input_power = final_output_power + total_loss
        
        # --- Voltage Calculation with Inductance ---
        electrical_omega = motor_omega_rad_s * p['pole_pairs']
        
        if p['wiring_type'] == 'star':
            # Line-to-line values
            back_emf = np.sqrt(3) * self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2)
            inductive_v_drop = current * electrical_omega * (p['phase_inductance'] * 2)
        else: # delta
            # Line-to-line values
            back_emf = self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2 / 3)
            inductive_v_drop = current * electrical_omega * (p['phase_inductance'] * 2 / 3)

        # Vector sum for voltage calculation
        # V = sqrt((V_bemf + V_r)^2 + V_l^2) - a simplification
        voltage = np.sqrt((back_emf + resistance_drop)**2 + inductive_v_drop**2)

        efficiency = np.divide(final_output_power, input_power, out=np.zeros_like(input_power), where=input_power > 0)
        
        return {
            '出力パワー': final_output_power,
            '全損失': total_loss,
            '総合効率': efficiency,
            'トルク': gearbox_output_torque,
            '必要電圧': voltage,
            '電流': current,
            '回転数': rpm
        }

class Application(tk.Frame):
    """GUIアプリケーションクラス"""
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("QDDモーター特性モデリングツール 3D版")
        self.pack(fill='both', expand=True)
        self.results = None
        self.Z_AXIS_MAP = {
            '総合効率 [%]': '総合効率',
            'トルク [Nm]': 'トルク',
            '出力パワー [W]': '出力パワー',
            '必要電圧 [V]': '必要電圧',
            '全損失 [W]': '全損失'
        }
        self.summary_layout = {
            "ピーク性能": [
                ("最大総合効率", "max_eff_val"),
                ("└ 回転数/電流/トルク", "max_eff_point"),
                ("最大出力パワー", "max_power_val"),
                ("└ 回転数/電流/トルク", "max_power_point"),
                ("最大トルク", "max_torque_val"),
                ("└ 回転数/電流", "max_torque_point")
            ],
            "定格動作時 (連続電流)": [
                ("最大効率", "rated_eff_val"),
                ("└ 回転数/トルク/パワー", "rated_point")
            ]
        }
        self.create_widgets()
        self.load_default_preset()

    def load_default_preset(self):
        """Load default.json at startup if it exists."""
        default_preset_path = 'default.json'
        if os.path.exists(default_preset_path):
            try:
                with open(default_preset_path, 'r', encoding='utf-8') as f:
                    loaded_params = json.load(f)
                for key, value in loaded_params.items():
                    if key in self.params:
                        self.params[key].set(value)
            except Exception as e:
                print(f"Info: Could not load default preset '{default_preset_path}': {e}")

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side='left', fill='y', padx=5, pady=5)

        params_frame = ttk.Labelframe(left_panel, text="モーターパラメータ", padding=10)
        params_frame.pack(fill='x', expand=True)

        self.fig = plt.Figure(figsize=(8, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)

        self.params = {}
        param_defs = {
            "モーター基本特性": {
                'kv': ('KV値 [rpm/V]', 100.0),
                'phase_resistance': ('一相あたり抵抗 (25℃) [Ohm]', 0.1),
                'phase_inductance': ('一相あたりインダクタンス [H]', 0.0001),
                'pole_pairs': ('極対数', 7.0),
                'wiring_type': ('配線方式', 'star', ['star', 'delta']),
                'continuous_current': ('連続電流 [A]', 10.0),
                'peak_current': ('ピーク電流 [A]', 30.0),
            },
            "熱モデル": {
                'ambient_temperature': ('周囲温度 [°C]', 25.0),
                'thermal_resistance': ('モーター熱抵抗 [°C/W]', 2.0),
            },
            "鉄損モデル": {
                'hysteresis_coeff': ('ヒステリシス係数 [W/rpm]', 0.001),
                'eddy_current_coeff': ('渦電流係数 [W/rpm^2]', 1e-7)
            },
            "ドライバ損失モデル": {
                'driver_on_resistance': ('ドライバON抵抗 [Ohm]', 0.005),
                'driver_fixed_loss': ('ドライバ固定損失 [W]', 2.0)
            },
            "ギア損失モデル": {
                'gear_ratio': ('減速比', 9.0),
                'gear_efficiency': ('ギア効率', 0.95)
            },
             "動作条件": {
                'bus_voltage': ('バス電圧 [V]', 48.0)
            }
        }

        row_counter = 0
        for section, fields in param_defs.items():
            ttk.Label(params_frame, text=section, font=('TkDefaultFont', 10, 'bold')).grid(row=row_counter, columnspan=4, pady=(10,2), sticky='w')
            row_counter += 1
            
            field_items = list(fields.items())
            for i, (key, value) in enumerate(field_items):
                row = row_counter + (i // 2)
                col_offset = (i % 2) * 2
                
                label = ttk.Label(params_frame, text=value[0])
                label.grid(row=row, column=col_offset, sticky='w', padx=5, pady=2)
                
                if isinstance(value[2], list) if len(value) > 2 else False:
                    self.params[key] = tk.StringVar(value=value[1])
                    widget = ttk.Combobox(params_frame, textvariable=self.params[key], values=value[2], width=10)
                else:
                    self.params[key] = tk.DoubleVar(value=value[1])
                    widget = ttk.Entry(params_frame, textvariable=self.params[key], width=12)
                
                widget.grid(row=row, column=col_offset + 1, sticky='e', padx=5, pady=2)

            row_counter += (len(field_items) + 1) // 2

        ttk.Label(params_frame, text="グラフZ軸(色/高さ)", font=('TkDefaultFont', 10, 'bold')).grid(row=row_counter, columnspan=2, pady=(10,2), sticky='w')
        row_counter += 1
        self.z_axis_var = tk.StringVar(value='総合効率 [%]')
        ttk.Combobox(params_frame, textvariable=self.z_axis_var, values=list(self.Z_AXIS_MAP.keys()), width=20).grid(row=row_counter, columnspan=2, sticky='w', padx=5, pady=2)
        row_counter += 1

        summary_frame = ttk.Labelframe(left_panel, text="サマリー", padding=10)
        summary_frame.pack(fill='x', expand=True, pady=10)
        self.summary_vars = {}
        
        s_row = 0
        for section, items in self.summary_layout.items():
            ttk.Label(summary_frame, text=section, font=('TkDefaultFont', 9, 'bold')).grid(row=s_row, columnspan=2, pady=(5,2), sticky='w')
            s_row += 1
            for display_text, internal_key in items:
                is_sub_item = display_text.startswith('└')
                text = display_text.lstrip('└ ')
                col = 1 if is_sub_item else 0
                
                ttk.Label(summary_frame, text=text+":").grid(row=s_row, column=0, sticky='w', padx=(20 if is_sub_item else 5))
                self.summary_vars[internal_key] = tk.StringVar(value="-")
                ttk.Label(summary_frame, textvariable=self.summary_vars[internal_key]).grid(row=s_row, column=1, sticky='w')
                s_row += 1

        calc_button = ttk.Button(left_panel, text="計算＆プロット", command=self.run_analysis)
        calc_button.pack(pady=10)
        
        preset_frame = ttk.Frame(left_panel)
        preset_frame.pack(pady=5)
        load_preset_button = ttk.Button(preset_frame, text="プリセット読込", command=self.load_preset)
        load_preset_button.pack(side='left', padx=5)
        save_preset_button = ttk.Button(preset_frame, text="プリセット保存", command=self.save_preset)
        save_preset_button.pack(side='left', padx=5)

        output_frame = ttk.Frame(left_panel)
        output_frame.pack(pady=5)
        png_button = ttk.Button(output_frame, text="PNG出力", command=self.save_as_png)
        png_button.pack(side='left', padx=5)
        summary_button = ttk.Button(output_frame, text="サマリー出力", command=self.save_summary)
        summary_button.pack(side='left', padx=5)

    def get_params(self):
        return {key: var.get() for key, var in self.params.items()}

    def run_analysis(self):
        params = self.get_params()
        model = MotorModel(params)

        z_axis_display = self.z_axis_var.get()
        z_axis_key = self.Z_AXIS_MAP[z_axis_display]

        if params['wiring_type'] == 'star':
            ke_line = model.ke * np.sqrt(3)
        else: # delta
            ke_line = model.ke
        
        if ke_line > 0:
            motor_rpm_unloaded = params['bus_voltage'] / ke_line * (60 / (2 * np.pi))
            theoretical_max_rpm = motor_rpm_unloaded / params['gear_ratio']
        else:
            theoretical_max_rpm = 5000

        current_range = np.linspace(0.1, params['peak_current'], 50)
        rpm_range = np.linspace(0.1, theoretical_max_rpm * 1.1, 50)
        I, RPM = np.meshgrid(current_range, rpm_range)

        results = model.analyze(I, RPM)
        self.results = results

        # --- サマリー計算 ---
        valid_mask = results['必要電圧'] <= params['bus_voltage']
        
        def get_summary_stats(key):
            if not np.any(valid_mask): return None, None  # noqa: E701
            data = np.where(valid_mask, results[key], np.nan)
            if not np.any(~np.isnan(data)): return None, None
            idx = np.nanargmax(data)
            coords = np.unravel_index(idx, data.shape)
            val = data[coords]
            return val, coords

        max_eff, eff_coords = get_summary_stats('総合効率')
        if max_eff is not None:
            self.summary_vars["max_eff_val"].set(f"{max_eff*100:.1f} %")
            self.summary_vars["max_eff_point"].set(f"{results['回転数'][eff_coords]:.0f} RPM / {results['電流'][eff_coords]:.1f} A / {results['トルク'][eff_coords]:.2f} Nm")

        max_power, power_coords = get_summary_stats('出力パワー')
        if max_power is not None:
            self.summary_vars["max_power_val"].set(f"{max_power:.1f} W")
            self.summary_vars["max_power_point"].set(f"{results['回転数'][power_coords]:.0f} RPM / {results['電流'][power_coords]:.1f} A / {results['トルク'][power_coords]:.2f} Nm")

        max_torque, torque_coords = get_summary_stats('トルク')
        if max_torque is not None:
            self.summary_vars["max_torque_val"].set(f"{max_torque:.2f} Nm")
            self.summary_vars["max_torque_point"].set(f"{results['回転数'][torque_coords]:.0f} RPM / {results['電流'][torque_coords]:.1f} A")

        cont_curr_idx = np.argmin(np.abs(current_range - params['continuous_current']))
        rated_mask = valid_mask[:, cont_curr_idx]
        rated_eff_slice = np.where(rated_mask, results['総合効率'][:, cont_curr_idx], np.nan)
        if np.any(~np.isnan(rated_eff_slice)):
            rated_idx = np.nanargmax(rated_eff_slice)
            self.summary_vars["rated_eff_val"].set(f"{rated_eff_slice[rated_idx]*100:.1f} %")
            self.summary_vars["rated_point"].set(f"{RPM[rated_idx, cont_curr_idx]:.0f} RPM / {results['トルク'][rated_idx, cont_curr_idx]:.2f} Nm / {results['出力パワー'][rated_idx, cont_curr_idx]:.1f} W")
        else:
            self.summary_vars["rated_eff_val"].set("-")
            self.summary_vars["rated_point"].set("-")

        # --- 3Dグラフ描画 ---
        Z = results[z_axis_key].copy()
        if z_axis_key == '総合効率': Z *= 100
        Z[~valid_mask] = np.nan

        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.ax.plot_surface(I, RPM, Z, cmap='plasma', rstride=1, cstride=1, alpha=0.9, antialiased=True, linewidth=0)

        self.ax.set_xlabel('電流 [A]')
        self.ax.set_ylabel('回転数 [RPM]')
        self.ax.set_zlabel(z_axis_display)
        self.ax.set_title(f'QDDモーター特性マップ: {z_axis_display}', pad=20)

        self.canvas.draw()

    def save_as_png(self):
        from tkinter.filedialog import asksaveasfilename
        from tkinter.messagebox import showerror
        filepath = asksaveasfilename(defaultextension=".png", filetypes=[("PNGファイル", "*.png"), ("すべてのファイル", "*.*")], title="グラフを保存")
        if not filepath: return
        try:
            self.fig.savefig(filepath, dpi=300, facecolor='white')
        except Exception as e:
            showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")

    def save_summary(self):
        """計算されたサマリーをテキストファイルとして保存する"""
        if self.results is None:
            messagebox.showwarning("データなし", "先に「計算＆プロット」を実行してください。")
            return

        from tkinter.filedialog import asksaveasfilename
        from tkinter.messagebox import showinfo
        filepath = asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            title="サマリーを保存"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("モーター性能サマリー\n")
                f.write("="*30 + "\n\n")
                
                f.write("【入力パラメータ】\n")
                params = self.get_params()
                for key, value in params.items():
                    f.write(f"- {key}: {value}\n")
                f.write("\n")

                for section, items in self.summary_layout.items():
                    f.write(f"【{section}】\n")
                    for display_text, internal_key in items:
                        value = self.summary_vars[internal_key].get()
                        f.write(f"- {display_text}: {value}\n")
                    f.write("\n")
            
            showinfo("保存完了", f"サマリーを {filepath} に保存しました。")

        except Exception as e:
            from tkinter.messagebox import showerror
            showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")

    def save_preset(self):
        """Save the current parameters to a JSON file."""
        from tkinter.filedialog import asksaveasfilename
        
        filepath = asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="プリセットを保存"
        )
        if not filepath:
            return

        try:
            params_to_save = self.get_params()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(params_to_save, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("保存完了", f"プリセットを {filepath} に保存しました。")
        except Exception as e:
            messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")

    def load_preset(self):
        """Load parameters from a JSON file."""
        from tkinter.filedialog import askopenfilename

        filepath = askopenfilename(
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
            title="プリセットを開く"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_params = json.load(f)
            
            for key, value in loaded_params.items():
                if key in self.params:
                    self.params[key].set(value)
                else:
                    print(f"Warning: Loaded parameter '{key}' not found in the GUI.")
            
            messagebox.showinfo("読込完了", "プリセットを読み込みました。")

        except json.JSONDecodeError:
            messagebox.showerror("読込エラー", "JSONファイルとして解析できませんでした。")
        except Exception as e:
            messagebox.showerror("読込エラー", f"ファイルの読み込み中にエラーが発生しました:\n{e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
