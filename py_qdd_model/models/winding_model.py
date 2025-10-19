import math
from typing import Dict, Any

# --- Built-in Reference Profiles ---
BUILTIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "min": {
        "description": "Small drone/hobby motor",
        "kv": 3000.0,
        "peak_current": 10.0,
        "phase_resistance": 0.2,
        "phase_inductance": 0.04
    },
    "small": {
        "description": "Mid-size drone/robot joint motor",
        "kv": 800.0,
        "peak_current": 20.0,
        "phase_resistance": 0.15,
        "phase_inductance": 0.07
    },
    "medium": {
        "description": "Default QDD-style robot actuator",
        "kv": 100.0,
        "peak_current": 30.0,
        "phase_resistance": 0.1,
        "phase_inductance": 0.1
    },
    "large": {
        "description": "Large robot actuator / e-bike hub motor",
        "kv": 50.0,
        "peak_current": 60.0,
        "phase_resistance": 0.05,
        "phase_inductance": 0.2
    },
    "max": {
        "description": "Very large direct drive motor",
        "kv": 20.0,
        "peak_current": 150.0,
        "phase_resistance": 0.02,
        "phase_inductance": 0.3
    }
}

# --- Constants ---
COPPER_RESISTIVITY = 1.68e-8  # Ohm*m

def estimate_new_winding(target_params: Dict[str, float], reference_params: Dict[str, float], density: float) -> Dict[str, float]:
    """
    Estimates new winding properties based on a target and reference motor.

    Args:
        target_params: Dictionary with target motor parameters (requires 'kv', 'peak_current').
        reference_params: Dictionary with reference motor parameters (requires 'kv', 'peak_current', 'phase_resistance', 'phase_inductance').
        density: Target current density in A/mm^2.

    Returns:
        A dictionary with the calculated nominal properties.
    """
    # Validate required keys
    required_keys_ref = ["kv", "peak_current", "phase_resistance", "phase_inductance"]
    required_keys_target = ["kv", "peak_current"]
    for key in required_keys_ref:
        if key not in reference_params:
            raise KeyError(f"Reference data is missing required key: '{key}'")
    for key in required_keys_target:
        if key not in target_params:
            raise KeyError(f"Target data is missing required key: '{key}'")

    # --- Core Calculation ---
    area_target_m2 = target_params["peak_current"] / (density * 1e6)
    area_ref_m2 = reference_params["peak_current"] / (density * 1e6)
    length_ref = (reference_params["phase_resistance"] * area_ref_m2) / COPPER_RESISTIVITY
    turn_ratio = reference_params["kv"] / target_params["kv"]
    
    estimated_length = length_ref * turn_ratio
    estimated_resistance = COPPER_RESISTIVITY * estimated_length / area_target_m2
    estimated_inductance = reference_params["phase_inductance"] * (turn_ratio ** 2)
    diameter_mm = 2 * math.sqrt(area_target_m2 / math.pi) * 1000

    return {
        "diameter_mm": diameter_mm,
        "length": estimated_length,
        "resistance": estimated_resistance,
        "inductance": estimated_inductance
    }
