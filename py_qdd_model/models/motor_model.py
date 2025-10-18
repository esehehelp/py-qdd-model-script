import numpy as np
from ..schema import MotorParams
from .copper_loss import CopperLossModel
from .iron_loss import IronLossModel
from .driver_loss import DriverLossModel
from .gear_loss import GearLossModel

class MotorModel:
    COPPER_TEMP_COEFF = 0.00393

    def __init__(self, params: MotorParams):
        self.p = params
        self.kt = 9.549 / self.p.kv
        self.ke = self.kt
        self.copper_model = CopperLossModel(self.p.wiring_type)
        # alphaを追加で受け取るように修正
        self.iron_model = IronLossModel(
            self.p.hysteresis_coeff,
            self.p.eddy_current_coeff,
            getattr(self.p, "steinmetz_alpha", 1.6),  # αはデフォルト1.6
            self.p.pole_pairs
        )
        self.driver_model = DriverLossModel(self.p.driver_on_resistance, self.p.driver_fixed_loss)
        self.gear_model = GearLossModel(self.p.gear_ratio, self.p.gear_efficiency)

    # --------------------------------------------------------
    # 内部ユーティリティ
    # --------------------------------------------------------
    def _to_motor_rpm(self, shaft_rpm):
        return shaft_rpm * self.p.gear_ratio

    def _omega_from_rpm(self, rpm):
        return rpm * (2 * np.pi / 60)

    def _estimate_flux_density(self, motor_rpm: np.ndarray) -> np.ndarray:
        """
        最大磁束密度BmaxをRPMに基づいて推定する。
        簡易モデル: Bmax = kB * (V / (f * N * A)) ∝ 1/f
        → RPMが上がるとBmaxが下がる傾向を反映。
        """
        f = np.maximum((motor_rpm * self.p.pole_pairs) / 60.0, 1e-3)
        # 定数スケーリング係数: 実験的に合わせる
        kB = getattr(self.p, "bmax_coeff", 0.3)
        return kB / np.sqrt(f / np.max(f))

    def _voltage_line_values(self, motor_omega_rad_s, current, phase_resistance):
        electrical_omega = motor_omega_rad_s * self.p.pole_pairs
        if self.p.wiring_type == 'star':
            back_emf = np.sqrt(3) * self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2)
            inductive_v_drop = current * electrical_omega * (self.p.phase_inductance * 2)
        else:
            back_emf = self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2 / 3)
            inductive_v_drop = current * electrical_omega * (self.p.phase_inductance * 2 / 3)
        voltage = np.sqrt((back_emf + resistance_drop) ** 2 + inductive_v_drop ** 2)
        return voltage

    # --------------------------------------------------------
    # メイン解析関数
    # --------------------------------------------------------
    def analyze(self, current: np.ndarray, shaft_rpm: np.ndarray, iters: int = 20):
        current = np.asarray(current)
        shaft_rpm = np.asarray(shaft_rpm)

        motor_rpm = self._to_motor_rpm(shaft_rpm)
        motor_omega = self._omega_from_rpm(motor_rpm)
        shaft_omega = self._omega_from_rpm(shaft_rpm)

        # 初期抵抗
        phase_resistance = np.full_like(current, self.p.phase_resistance, dtype=float)
        motor_temp = np.full_like(current, self.p.ambient_temperature, dtype=float)

        # === 反復温度収束ループ ===
        for _ in range(iters):
            prev_motor_temp = motor_temp.copy()

            Bmax = self._estimate_flux_density(motor_rpm)

            copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
            iron_loss = self.iron_model.calculate_loss(motor_rpm, Bmax)
            driver_loss = self.driver_model.calculate_loss(current)

            gross_torque = self.kt * current
            torque_loss_iron = np.divide(iron_loss, motor_omega, out=np.zeros_like(motor_omega), where=motor_omega > 0)
            motor_output_torque = np.maximum(0.0, gross_torque - torque_loss_iron)
            motor_output_power = motor_output_torque * motor_omega

            gear_loss_est, _ = self.gear_model.calculate_loss(motor_output_power)
            total_loss = copper_loss + iron_loss + driver_loss + gear_loss_est

            motor_temp = self.p.ambient_temperature + total_loss * self.p.thermal_resistance
            phase_resistance = self.p.phase_resistance * (1 + self.COPPER_TEMP_COEFF * (motor_temp - 25.0))

            # 温度が収束したらループを抜ける
            if np.all(np.abs(motor_temp - prev_motor_temp) < 0.1):
                break

        # === 最終出力 ===
        copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
        Bmax = self._estimate_flux_density(motor_rpm)
        iron_loss = self.iron_model.calculate_loss(motor_rpm, Bmax)
        driver_loss = self.driver_model.calculate_loss(current)

        gross_torque = self.kt * current
        torque_loss_iron = np.divide(iron_loss, motor_omega, out=np.zeros_like(motor_omega), where=motor_omega > 0)
        motor_output_torque = np.maximum(0.0, gross_torque - torque_loss_iron)
        motor_output_power = motor_output_torque * motor_omega

        gear_loss, final_output_power = self.gear_model.calculate_loss(motor_output_power)
        shaft_output_torque = np.divide(final_output_power, shaft_omega, out=np.zeros_like(shaft_omega), where=shaft_omega > 0)

        total_loss = copper_loss + iron_loss + driver_loss + gear_loss
        input_power = final_output_power + total_loss

        voltage = self._voltage_line_values(motor_omega, current, phase_resistance)
        efficiency = np.divide(final_output_power, input_power, out=np.zeros_like(input_power), where=input_power > 0)

        return {
            'output_power': final_output_power,
            'total_loss': total_loss,
            'efficiency': efficiency,
            'torque': shaft_output_torque,
            'voltage': voltage,
            'current': current,
            'rpm': shaft_rpm,
            'Bmax': Bmax
        }
