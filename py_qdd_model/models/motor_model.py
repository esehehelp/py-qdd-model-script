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
        self.iron_model = IronLossModel(self.p.hysteresis_coeff, self.p.eddy_current_coeff)
        self.driver_model = DriverLossModel(self.p.driver_on_resistance, self.p.driver_fixed_loss)
        self.gear_model = GearLossModel(self.p.gear_ratio, self.p.gear_efficiency)

    def _to_motor_rpm(self, shaft_rpm):
        return shaft_rpm * self.p.gear_ratio

    def _omega_from_rpm(self, rpm):
        return rpm * (2 * np.pi / 60)

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

    def analyze(self, current: np.ndarray, shaft_rpm: np.ndarray, iters: int = 20):
        """ベクトル化された current (A) と shaft_rpm (RPM) のグリッドを受け取り、
        主要出力を辞書で返す（ndarrayを含む）。
        """
        # Validate shapes
        current = np.asarray(current)
        shaft_rpm = np.asarray(shaft_rpm)

        motor_rpm = self._to_motor_rpm(shaft_rpm)
        motor_omega = self._omega_from_rpm(motor_rpm)
        shaft_omega = self._omega_from_rpm(shaft_rpm)

        # initialize phase resistance grid
        phase_resistance = np.full_like(current, self.p.phase_resistance, dtype=float)

        for _ in range(iters):
            copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
            iron_loss = self.iron_model.calculate_loss(motor_rpm)
            driver_loss = self.driver_model.calculate_loss(current)

            gross_torque = self.kt * current
            torque_loss_iron = np.divide(iron_loss, motor_omega, out=np.zeros_like(motor_omega, dtype=float), where=motor_omega>0)
            motor_output_torque = gross_torque - torque_loss_iron
            motor_output_torque = np.maximum(0.0, motor_output_torque)
            motor_output_power = motor_output_torque * motor_omega

            gear_loss_est, _ = self.gear_model.calculate_loss(motor_output_power)
            total_loss = copper_loss + iron_loss + driver_loss + gear_loss_est

            motor_temp = self.p.ambient_temperature + total_loss * self.p.thermal_resistance
            phase_resistance = self.p.phase_resistance * (1 + self.COPPER_TEMP_COEFF * (motor_temp - 25.0))

        # final calculations
        copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
        iron_loss = self.iron_model.calculate_loss(motor_rpm)
        driver_loss = self.driver_model.calculate_loss(current)

        gross_torque = self.kt * current
        torque_loss_iron = np.divide(iron_loss, motor_omega, out=np.zeros_like(motor_omega, dtype=float), where=motor_omega>0)
        motor_output_torque = gross_torque - torque_loss_iron
        motor_output_torque = np.maximum(0.0, motor_output_torque)
        motor_output_power = motor_output_torque * motor_omega

        gear_loss, final_output_power = self.gear_model.calculate_loss(motor_output_power)
        # shaft output torque
        shaft_output_torque = np.divide(final_output_power, shaft_omega, out=np.zeros_like(shaft_omega, dtype=float), where=shaft_omega>0)

        total_loss = copper_loss + iron_loss + driver_loss + gear_loss
        input_power = final_output_power + total_loss

        voltage = self._voltage_line_values(motor_omega, current, phase_resistance)
        efficiency = np.divide(final_output_power, input_power, out=np.zeros_like(input_power, dtype=float), where=input_power>0)

        return {
            'output_power': final_output_power,
            'total_loss': total_loss,
            'efficiency': efficiency,
            'torque': shaft_output_torque,
            'voltage': voltage,
            'current': current,
            'rpm': shaft_rpm
        }
