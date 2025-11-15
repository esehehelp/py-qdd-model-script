import numpy as np
from typing import Dict, Tuple
import numpy.typing as npt
from ..schema import MotorParams
from .copper_loss import CopperLossModel
from .iron_loss import IronLossModel
from .driver_loss import DriverLossModel
from .gear_loss import GearLossModel
from .. import constants as C

class MotorModel:

    def __init__(self, params: MotorParams):
        # Create a deep copy of the params to avoid modifying the original
        self.p = params.model_copy(deep=True)
        
        # Convert inductance from uH (application-wide unit) to H (physics unit)
        # Pydantic models are immutable, so we create a new model with the updated value.
        new_winding_params = self.p.winding.model_copy(
            update={'phase_inductance': self.p.winding.phase_inductance / 1e6}
        )
        self.p = self.p.model_copy(update={'winding': new_winding_params})

        self.kt = C.PhysicsConstants.RAD_PER_SEC_TO_RPM / self.p.electrical.kv
        self.ke = self.kt
        self.copper_model = CopperLossModel(self.p.winding.wiring_type)
        self.iron_model = IronLossModel(
            kh=self.p.electrical.hysteresis_coeff,
            ke=self.p.electrical.eddy_current_coeff,
            # The following are optional legacy params, so we use getattr
            alpha=getattr(self.p.electrical, "steinmetz_alpha", 2.0),
            beta=getattr(self.p.electrical, "steinmetz_beta", 1.5),
            kg=getattr(self.p.electrical, "steinmetz_kg", None),
            pole_pairs=self.p.magnets.pole_pairs
        )
        self.driver_model = DriverLossModel(self.p.driver.driver_on_resistance, self.p.driver.driver_fixed_loss)
        self.gear_model = GearLossModel(self.p.gear.gear_ratio, self.p.gear.gear_efficiency)

    def _to_motor_rpm(self, shaft_rpm: npt.NDArray) -> npt.NDArray:
        return shaft_rpm * self.p.gear.gear_ratio

    def _omega_from_rpm(self, rpm: npt.NDArray) -> npt.NDArray:
        return rpm * C.PhysicsConstants.RPM_TO_RAD_PER_SEC

    def _estimate_flux_density(self, motor_rpm: npt.NDArray, voltage_available: float = None, current: npt.NDArray = None, motor_temp: npt.NDArray = None) -> npt.NDArray:
        motor_rpm = np.asarray(motor_rpm)
        f = np.maximum((motor_rpm * self.p.magnets.pole_pairs) / 60.0, 1e-6)
        # TODO: Replace this crude estimation with a more physics-based model
        kB = getattr(self.p.magnets, "bmax_coeff", 0.3)
        B_base = kB / np.sqrt(f / np.max(f))

        if voltage_available is not None:
            omega = motor_rpm * C.PhysicsConstants.RPM_TO_RAD_PER_SEC
            emf = self.ke * omega
            scale = np.minimum(1.0, voltage_available / (np.maximum(emf, 1e-6)))
            B_base = B_base * scale

        if motor_temp is not None:
            tcoeff = getattr(self.p.magnets, "magnet_temp_coeff", -0.002)
            demag = 1.0 + tcoeff * (motor_temp - C.PhysicsConstants.REFERENCE_TEMPERATURE)
            demag = np.maximum(0.5, demag)
            B_base = B_base * demag

        return B_base

    def _voltage_line_values(self, motor_omega_rad_s: npt.NDArray, current: npt.NDArray, phase_resistance: npt.NDArray) -> npt.NDArray:
        electrical_omega = motor_omega_rad_s * self.p.magnets.pole_pairs
        if self.p.winding.wiring_type == 'star':
            back_emf = np.sqrt(3) * self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2)
            inductive_v_drop = current * electrical_omega * (self.p.winding.phase_inductance * 2)
        else: # delta
            back_emf = self.ke * motor_omega_rad_s
            resistance_drop = current * (phase_resistance * 2 / 3)
            inductive_v_drop = current * electrical_omega * (self.p.winding.phase_inductance * 2 / 3)
        voltage = np.sqrt((back_emf + resistance_drop) ** 2 + inductive_v_drop ** 2)
        return voltage

    def _calculate_all_losses(self, state: Dict[str, npt.NDArray], Bmax: npt.NDArray) -> Tuple[Dict[str, npt.NDArray], npt.NDArray]:
        """Calculates all losses and the final output power."""
        copper_loss = self.copper_model.calculate_loss(state["current"], state["phase_resistance"])
        iron_loss = self.iron_model.calculate_loss(state["motor_rpm"], Bmax)
        driver_loss = self.driver_model.calculate_loss(state["current"])

        gross_torque = self.kt * state["current"]
        torque_loss_iron = np.zeros_like(state["motor_omega"])
        np.divide(iron_loss, state["motor_omega"], out=torque_loss_iron, where=state["omega_pos_mask"])
        motor_output_torque = np.maximum(0.0, gross_torque - torque_loss_iron)
        motor_output_power = motor_output_torque * state["motor_omega"]

        gear_loss, final_output_power = self.gear_model.calculate_loss(motor_output_power)

        losses = {
            "copper": copper_loss,
            "iron": iron_loss,
            "driver": driver_loss,
            "gear": gear_loss
        }
        return losses, final_output_power

    def _initialize_analysis(self, current: npt.NDArray, shaft_rpm: npt.NDArray) -> Dict[str, npt.NDArray]:
        """Prepares the initial state for the analysis."""
        current = np.asarray(current)
        shaft_rpm = np.asarray(shaft_rpm)
        motor_rpm = self._to_motor_rpm(shaft_rpm)
        motor_omega = self._omega_from_rpm(motor_rpm)

        return {
            "current": current,
            "shaft_rpm": shaft_rpm,
            "motor_rpm": motor_rpm,
            "motor_omega": motor_omega,
            "shaft_omega": self._omega_from_rpm(shaft_rpm),
            "phase_resistance": np.full_like(current, self.p.winding.phase_resistance, dtype=float),
            "motor_temp": np.full_like(current, self.p.thermal.ambient_temperature, dtype=float),
            "omega_pos_mask": motor_omega > 0,
        }

    def _iterate_thermal_equilibrium(self, state: Dict[str, npt.NDArray], iters: int, relax: float) -> Dict[str, npt.NDArray]:
        """Iteratively calculates losses and temperature until thermal equilibrium is reached."""
        for _ in range(iters):
            prev_temp = state["motor_temp"].copy()

            Bmax = self._estimate_flux_density(state["motor_rpm"], voltage_available=self.p.simulation.bus_voltage, current=state["current"], motor_temp=state["motor_temp"])
            
            losses, _ = self._calculate_all_losses(state, Bmax)
            total_loss = sum(losses.values())

            new_temp = self.p.thermal.ambient_temperature + total_loss * self.p.thermal.thermal_resistance
            state["motor_temp"] = prev_temp + relax * (new_temp - prev_temp)
            
            state["phase_resistance"] = self.p.winding.phase_resistance * (1 + C.PhysicsConstants.COPPER_TEMP_COEFF * (state["motor_temp"] - C.PhysicsConstants.REFERENCE_TEMPERATURE))

            if np.all(np.abs(state["motor_temp"] - prev_temp) < C.ModelDefaults.CONVERGENCE_THRESHOLD):
                break
        
        state["Bmax"] = self._estimate_flux_density(state["motor_rpm"], voltage_available=self.p.simulation.bus_voltage, current=state["current"], motor_temp=state["motor_temp"])
        return state

    def _calculate_final_results(self, state: Dict[str, npt.NDArray]) -> Dict[str, npt.NDArray]:
        """Calculates the final performance metrics from the converged state."""
        losses, final_output_power = self._calculate_all_losses(state, state["Bmax"])
        total_loss = sum(losses.values())

        shaft_output_torque = np.divide(final_output_power, state["shaft_omega"], out=np.zeros_like(state["shaft_omega"]), where=state["shaft_omega"] > 0)
        input_power = final_output_power + total_loss

        voltage = self._voltage_line_values(state["motor_omega"], state["current"], state["phase_resistance"])
        efficiency = np.divide(final_output_power, input_power, out=np.zeros_like(input_power), where=input_power > 0)

        return {
            'output_power': final_output_power,
            'total_loss': total_loss,
            'efficiency': efficiency,
            'torque': shaft_output_torque,
            'voltage': voltage,
            'current': state["current"],
            'rpm': state["shaft_rpm"],
            'Bmax': state["Bmax"],
            'motor_temp': state["motor_temp"]
        }

    def analyze(self, current: npt.NDArray, shaft_rpm: npt.NDArray, iters: int = C.ModelDefaults.MAX_ITERATIONS, relax: float = C.ModelDefaults.RELAXATION_FACTOR) -> Dict[str, npt.NDArray]:
        """
        Analyzes the motor performance by calculating thermal equilibrium and performance metrics.
        """
        initial_state = self._initialize_analysis(current, shaft_rpm)
        final_state = self._iterate_thermal_equilibrium(initial_state, iters, relax)
        results = self._calculate_final_results(final_state)
        return results