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
        # iron_model accepts kg/alpha/beta optionally
        self.iron_model = IronLossModel(
            kh=getattr(self.p, "hysteresis_coeff", 0.001),
            ke=getattr(self.p, "eddy_current_coeff", 1e-7),
            alpha=getattr(self.p, "steinmetz_alpha", 2.0),
            beta=getattr(self.p, "steinmetz_beta", 1.5),
            kg=getattr(self.p, "steinmetz_kg", None),
            pole_pairs=self.p.pole_pairs
        )
        self.driver_model = DriverLossModel(self.p.driver_on_resistance, self.p.driver_fixed_loss)
        self.gear_model = GearLossModel(self.p.gear_ratio, self.p.gear_efficiency)

    def _to_motor_rpm(self, shaft_rpm):
        return shaft_rpm * self.p.gear_ratio

    def _omega_from_rpm(self, rpm):
        return rpm * (2 * np.pi / 60)

    def _estimate_flux_density(self, motor_rpm: np.ndarray, voltage_available: float = None, current: np.ndarray = None, motor_temp: np.ndarray = None) -> np.ndarray:
        # (use the improved implementation from previous snippet)
        motor_rpm = np.asarray(motor_rpm)
        f = np.maximum((motor_rpm * self.p.pole_pairs) / 60.0, 1e-6)
        kB = getattr(self.p, "bmax_coeff", 0.3)
        B_base = kB / np.sqrt(f / np.max(f))

        if voltage_available is not None:
            omega = motor_rpm * (2 * np.pi / 60)
            emf = self.ke * omega
            scale = np.minimum(1.0, voltage_available / (np.maximum(emf, 1e-6)))
            B_base = B_base * scale

        if motor_temp is not None:
            tcoeff = getattr(self.p, "magnet_temp_coeff", -0.002)
            demag = 1.0 + tcoeff * (motor_temp - 25.0)
            demag = np.maximum(0.5, demag)
            B_base = B_base * demag

        return B_base

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

    def analyze(self, current: np.ndarray, shaft_rpm: np.ndarray, iters: int = 50, relax: float = 0.4):
        """
        Analyze returns results dict (same shape arrays) like before.
        Added:
          - relax: under-relaxation factor (0 < relax <= 1). Lower => more stable, slower.
        """
        current = np.asarray(current)
        shaft_rpm = np.asarray(shaft_rpm)

        motor_rpm = self._to_motor_rpm(shaft_rpm)
        motor_omega = self._omega_from_rpm(motor_rpm)
        shaft_omega = self._omega_from_rpm(shaft_rpm)

        phase_resistance = np.full_like(current, self.p.phase_resistance, dtype=float)
        motor_temp = np.full_like(current, self.p.ambient_temperature, dtype=float)

        # Precompute omega mask
        omega_pos_mask = motor_omega > 0

        for n in range(iters):
            # previous temperature (for relaxation)
            prev_temp = motor_temp.copy()

            # estimate flux density using current voltage availability (bus voltage)
            # approximate per-sample voltage availability = p.bus_voltage (simple)
            Bmax = self._estimate_flux_density(motor_rpm, voltage_available=self.p.bus_voltage, current=current, motor_temp=motor_temp)

            # loss computations (vectorized)
            copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
            iron_loss = self.iron_model.calculate_loss(motor_rpm, Bmax)
            driver_loss = self.driver_model.calculate_loss(current)

            gross_torque = self.kt * current
            # torque_loss_iron = iron_loss / motor_omega  (but zero where omega==0)
            torque_loss_iron = np.zeros_like(motor_omega)
            np.divide(iron_loss, motor_omega, out=torque_loss_iron, where=omega_pos_mask)

            motor_output_torque = np.maximum(0.0, gross_torque - torque_loss_iron)
            motor_output_power = motor_output_torque * motor_omega

            gear_loss_est, _ = self.gear_model.calculate_loss(motor_output_power)
            total_loss = copper_loss + iron_loss + driver_loss + gear_loss_est

            # new temp from loss
            new_temp = self.p.ambient_temperature + total_loss * self.p.thermal_resistance

            # under-relaxation
            motor_temp = prev_temp + relax * (new_temp - prev_temp)

            # update phase resistance
            phase_resistance = self.p.phase_resistance * (1 + self.COPPER_TEMP_COEFF * (motor_temp - 25.0))

            # convergence check
            if np.all(np.abs(motor_temp - prev_temp) < 0.05):
                break

        # final computations (same as before)
        copper_loss = self.copper_model.calculate_loss(current, phase_resistance)
        Bmax = self._estimate_flux_density(motor_rpm, voltage_available=self.p.bus_voltage, current=current, motor_temp=motor_temp)
        iron_loss = self.iron_model.calculate_loss(motor_rpm, Bmax)
        driver_loss = self.driver_model.calculate_loss(current)

        gross_torque = self.kt * current
        torque_loss_iron = np.zeros_like(motor_omega)
        np.divide(iron_loss, motor_omega, out=torque_loss_iron, where=omega_pos_mask)
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
            'Bmax': Bmax,
            'motor_temp': motor_temp
        }
