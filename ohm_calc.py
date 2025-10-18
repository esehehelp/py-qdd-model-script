import json
import argparse
import math
import pathlib

# --- Built-in Reference Profiles ---
BUILTIN_PROFILES = {
    "min": {
        "description": "Small drone/hobby motor",
        "kv": 3000.0,
        "peak_current": 10.0,
        "phase_resistance": 0.2,
        "phase_inductance": 30e-6
    },
    "small": {
        "description": "Mid-size drone/robot joint motor",
        "kv": 800.0,
        "peak_current": 20.0,
        "phase_resistance": 0.15,
        "phase_inductance": 70e-6
    },
    "medium": {
        "description": "Default QDD-style robot actuator",
        "kv": 100.0,
        "peak_current": 30.0,
        "phase_resistance": 0.1,
        "phase_inductance": 100e-6
    },
    "large": {
        "description": "Large robot actuator / e-bike hub motor",
        "kv": 50.0,
        "peak_current": 60.0,
        "phase_resistance": 0.05,
        "phase_inductance": 150e-6
    },
    "max": {
        "description": "Very large direct drive motor",
        "kv": 20.0,
        "peak_current": 150.0,
        "phase_resistance": 0.02,
        "phase_inductance": 200e-6
    }
}

# --- Constants ---
COPPER_RESISTIVITY = 1.68e-8  # Ohm*m

def calculate_estimates(p_target, p_ref, density):
    """Performs the core estimation calculation."""
    area_target_m2 = p_target["peak_current"] / (density * 1e6)
    area_ref_m2 = p_ref["peak_current"] / (density * 1e6)
    length_ref = (p_ref["phase_resistance"] * area_ref_m2) / COPPER_RESISTIVITY
    turn_ratio = p_ref["kv"] / p_target["kv"]
    
    estimated_length = length_ref * turn_ratio
    estimated_resistance = COPPER_RESISTIVITY * estimated_length / area_target_m2
    estimated_inductance = p_ref["phase_inductance"] * (turn_ratio ** 2)
    diameter_mm = 2 * math.sqrt(area_target_m2 / math.pi) * 1000

    return {
        "diameter_mm": diameter_mm,
        "length": estimated_length,
        "resistance": estimated_resistance,
        "inductance": estimated_inductance
    }

def main():
    parser = argparse.ArgumentParser(
        description="Estimate new winding properties based on a reference motor profile or file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target_preset_path",
        type=pathlib.Path,
        help="Path to the JSON preset file for the NEW motor design."
    )
    parser.add_argument(
        "--density",
        type=float,
        required=True,
        help="Target current density in A/mm^2 (e.g., 8.0)."
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--reference",
        type=pathlib.Path,
        help="Path to a custom reference motor JSON preset file."
    )
    group.add_argument(
        "--profile",
        type=str,
        choices=BUILTIN_PROFILES.keys(),
        help=f"Use a built-in reference profile. Choices: {list(BUILTIN_PROFILES.keys())}"
    )

    args = parser.parse_args()

    try:
        if not args.target_preset_path.is_file():
            raise FileNotFoundError(f"Target preset file not found at '{args.target_preset_path}'")
        with open(args.target_preset_path, 'r', encoding='utf-8') as f:
            p_target = json.load(f)

        ref_name = ""
        if args.profile:
            p_ref_base = BUILTIN_PROFILES[args.profile]
            ref_name = f"'{args.profile}' profile ({p_ref_base['description']})"
        elif args.reference:
            if not args.reference.is_file():
                raise FileNotFoundError(f"Reference preset file not found at '{args.reference}'")
            with open(args.reference, 'r', encoding='utf-8') as f:
                p_ref_base = json.load(f)
            ref_name = f"file '{args.reference.name}'"
        else:
            args.profile = "medium"
            p_ref_base = BUILTIN_PROFILES[args.profile]
            ref_name = f"default '{args.profile}' profile ({p_ref_base['description']})"

        required_keys_ref = ["kv", "peak_current", "phase_resistance", "phase_inductance"]
        required_keys_target = ["kv", "peak_current"]
        for key in required_keys_ref:
            if key not in p_ref_base:
                raise KeyError(f"Reference data ({ref_name}) is missing required key: '{key}'")
        for key in required_keys_target:
            if key not in p_target:
                raise KeyError(f"Target preset '{args.target_preset_path.name}' is missing required key: '{key}'")

        # --- Calculations with ±10% uncertainty on reference ---
        p_ref_low = {k: v * 0.9 for k, v in p_ref_base.items() if isinstance(v, (int, float))}
        p_ref_high = {k: v * 1.1 for k, v in p_ref_base.items() if isinstance(v, (int, float))}

        est_low = calculate_estimates(p_target, p_ref_low, args.density)
        est_high = calculate_estimates(p_target, p_ref_high, args.density)

        # --- Print Results ---
        print("--- Approximate Winding Calculation (with ±10% Reference Uncertainty) ---")
        print(f"Target: '{args.target_preset_path.name}' (KV: {p_target['kv']})")
        print(f"Reference: {ref_name} (KV: {p_ref_base['kv']})")
        print(f"Target Current Density: {args.density} A/mm^2")
        print("-" * 60)
        print("ASSUMPTIONS:")
        print("1. Target motor has the same physical geometry as the reference motor.")
        print("2. KV is inversely proportional to the number of turns.")
        print("3. Inductance is proportional to the square of the number of turns.")
        print("4. Reference motor is assumed to be designed with the same current density.")
        print("-" * 60)
        print("CALCULATED PROPERTIES FOR TARGET MOTOR:")
        print(f"  - Est. Wire Diameter:    {est_low['diameter_mm']:.3f} mm (This value is independent of reference uncertainty)")
        print(f"  - Est. Total Length:     {est_low['length']:.2f} - {est_high['length']:.2f} m")
        print(f"  - Est. Phase Resistance:  {est_low['resistance']:.4f} - {est_high['resistance']:.4f} Ohm")
        print(f"  - Est. Phase Inductance:  {est_low['inductance'] * 1e6:.2f} - {est_high['inductance'] * 1e6:.2f} uH")
        print("-" * 60)

    except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
