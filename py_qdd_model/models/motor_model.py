import numpy as np
from typing import Dict, Tuple, List, Any
import numpy.typing as npt
from ..schema import MotorAssembly, StatorComponent, RotorComponent, WindingComponent, MagnetComponent, Topology
from ..utils.material_manager import material_manager
from .copper_loss import CopperLossModel
from .iron_loss import IronLossModel
from .driver_loss import DriverLossModel
from .gear_loss import GearLossModel
from .. import constants as C

class MotorModel:

    def __init__(self, assembly: MotorAssembly):
        self.assembly = assembly
        self.components: Dict[str, Any] = {comp.name: comp for comp in assembly.components}
        self.topology = assembly.topology

        # Extract specific components for easier access
        self.stators: List[StatorComponent] = [c for c in assembly.components if isinstance(c, StatorComponent)]
        self.rotors: List[RotorComponent] = [c for c in assembly.components if isinstance(c, RotorComponent)]
        self.windings: List[WindingComponent] = [c for c in assembly.components if isinstance(c, WindingComponent)]
        self.magnets: List[MagnetComponent] = [c for c in assembly.components if isinstance(c, MagnetComponent)]

        # --- Material Data Lookup ---
        # This is a simplified example. In a full implementation, each component
        # would look up its specific material properties.
        self.core_material_data = {}
        if self.stators:
            # Assuming for now a single stator for core material properties
            stator = self.stators[0]
            self.core_material_data = material_manager.get_material("core_materials", stator.material_key)
            if not self.core_material_data:
                raise ValueError(f"Core material '{stator.material_key}' not found.")

        self.magnet_material_data = {}
        if self.magnets:
            # Assuming for now a single magnet type for magnet material properties
            magnet = self.magnets[0]
            self.magnet_material_data = material_manager.get_material("magnet_materials", magnet.material_key)
            if not self.magnet_material_data:
                raise ValueError(f"Magnet material '{magnet.material_key}' not found.")
        
        self.wire_material_data = {}
        if self.windings:
            # Assuming for now a single winding type for wire material properties
            winding = self.windings[0]
            self.wire_material_data = material_manager.get_material("wire_materials", winding.material_key)
            if not self.wire_material_data:
                raise ValueError(f"Wire material '{winding.material_key}' not found.")

        # --- Derive Basic Physical Constants (Placeholder) ---
        # These will need to be calculated based on the new component geometry and materials
        # For now, we'll use dummy values or derive from the first available component.
        
        # Example: Derive phase_resistance from wire material and winding geometry
        # This is a placeholder and needs detailed implementation based on winding geometry
        self.phase_resistance = 0.1 # Dummy value for now
        if self.windings and self.wire_material_data:
            winding = self.windings[0]
            # Placeholder: calculate actual wire length from geometry and turns
            wire_length_per_phase = winding.turns_per_coil * 200 # Example: 200mm per turn
            resistivity_at_20C = self.wire_material_data.get("resistance_per_km", 0.0) / 1000 # Ohm/m
            self.phase_resistance = resistivity_at_20C * wire_length_per_phase

        # Example: Derive kt/ke from magnet material and geometry
        # This is a complex calculation and will require a dedicated magnetic circuit model
        self.kt = 0.05 # Dummy value for now
        self.ke = self.kt

        # --- Initialize Loss Models (Placeholders) ---
        self.copper_model = CopperLossModel(self.windings[0].wiring_type if self.windings else 'star')
        
        # Iron loss model needs core material properties
        self.iron_model = IronLossModel(
            kh=self.core_material_data.get("loss_coefficients", {}).get("kh", 0.001),
            ke=self.core_material_data.get("loss_coefficients", {}).get("ke", 1e-7),
            pole_pairs=self.magnets[0].pole_pairs if self.magnets else 1 # Assuming first magnet component
        )
        
        # Driver and Gear models are less dependent on motor internal structure
        self.driver_model = DriverLossModel(0.005, 2.0) # Dummy values
        self.gear_model = GearLossModel(1.0, 1.0) # Dummy values

    def _to_motor_rpm(self, shaft_rpm: npt.NDArray) -> npt.NDArray:
        # This will need to be derived from the gear component if present
        return shaft_rpm * 1.0 # Dummy gear ratio

    def _omega_from_rpm(self, rpm: npt.NDArray) -> npt.NDArray:
        return rpm * C.PhysicsConstants.RPM_TO_RAD_PER_SEC

    def _estimate_flux_density(self, motor_rpm: npt.NDArray, voltage_available: float = None, current: npt.NDArray = None, motor_temp: npt.NDArray = None) -> npt.NDArray:
        # This will need to be a much more sophisticated model based on magnet geometry,
        # air gap, stator/rotor geometry, and material properties.
        return np.full_like(motor_rpm, 0.5) # Dummy value

    def _voltage_line_values(self, motor_omega_rad_s: npt.NDArray, current: npt.NDArray, phase_resistance: npt.NDArray) -> npt.NDArray:
        # This will need to be adapted to the new winding component properties
        return np.full_like(motor_omega_rad_s, 12.0) # Dummy value

    def _calculate_all_losses(self, state: Dict[str, npt.NDArray], Bmax: npt.NDArray) -> Tuple[Dict[str, npt.NDArray], npt.NDArray]:
        """Calculates all losses and the final output power."""
        # These calculations will need to be adapted to the new component structure
        copper_loss = self.copper_model.calculate_loss(state["current"], state["phase_resistance"])
        iron_loss = self.iron_model.calculate_loss(state["motor_rpm"], Bmax)
        driver_loss = self.driver_model.calculate_loss(state["current"])
        gear_loss, final_output_power = self.gear_model.calculate_loss(np.zeros_like(state["current"])) # Dummy input

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
            "phase_resistance": np.full_like(current, self.phase_resistance, dtype=float), # Use derived resistance
            "motor_temp": np.full_like(current, self.assembly.simulation.ambient_temperature, dtype=float),
            "omega_pos_mask": motor_omega > 0,
        }

    def _iterate_thermal_equilibrium(self, state: Dict[str, npt.NDArray], iters: int, relax: float) -> Dict[str, npt.NDArray]:
        """Iteratively calculates losses and temperature until thermal equilibrium is reached."""
        # This method will need to be adapted to the new component structure and thermal model
        for _ in range(iters):
            prev_temp = state["motor_temp"].copy()

            Bmax = self._estimate_flux_density(state["motor_rpm"], voltage_available=self.assembly.simulation.bus_voltage, current=state["current"], motor_temp=state["motor_temp"])
            
            losses, _ = self._calculate_all_losses(state, Bmax)
            total_loss = sum(losses.values())

            # Thermal resistance will need to be derived from components and materials
            thermal_resistance = self.assembly.override_thermal_resistance if self.assembly.override_thermal_resistance is not None else 2.0 # Dummy value
            new_temp = self.assembly.simulation.ambient_temperature + total_loss * thermal_resistance
            state["motor_temp"] = prev_temp + relax * (new_temp - prev_temp)
            
            # Phase resistance temperature dependency
            state["phase_resistance"] = self.phase_resistance * (1 + C.PhysicsConstants.COPPER_TEMP_COEFF * (state["motor_temp"] - C.PhysicsConstants.REFERENCE_TEMPERATURE))

            if np.all(np.abs(state["motor_temp"] - prev_temp) < C.ModelDefaults.CONVERGENCE_THRESHOLD):
                break
        
        state["Bmax"] = self._estimate_flux_density(state["motor_rpm"], voltage_available=self.assembly.simulation.bus_voltage, current=state["current"], motor_temp=state["motor_temp"])
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