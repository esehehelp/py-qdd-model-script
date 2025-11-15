import csv
import io
from ..schema import MotorParams
# from ..ui import constants as C_UI # 削除
# from ..i18n.translator import t # 削除

def _flatten_params(params: MotorParams, param_defs: dict):
    """
    Flattens the nested Pydantic model into a list of tuples for CSV export.
    (parameter_name, value, comment_string)
    """
    flat_list = []
    
    # Create a flat map from schema key to the label string for easier lookup
    param_labels = {}
    for group_fields in param_defs.values():
        for key, (label, *_) in group_fields.items():
            param_labels[key] = label

    def recurse(model_part, prefix=""):
        for field_name, value in model_part:
            param_name = f"{prefix}{field_name}"
            
            if isinstance(value, (int, float, str, bool)):
                # Try to find the label in param_defs, otherwise use the key name itself
                label = param_labels.get(field_name, param_name)
                comment = f"Unit: {label}"
                flat_list.append((param_name, value, comment))
            elif hasattr(value, 'model_dump'): # It's a nested Pydantic model
                recurse(value, prefix=f"{param_name}_")

    recurse(params)
    return flat_list

def export_params_to_fusion_csv(params: MotorParams, param_defs: dict) -> str:
    """
    Exports motor parameters to a CSV string compatible with Fusion 360.
    
    Args:
        params: The MotorParams object.
        param_defs: The UI parameter definitions for unit lookup.

    Returns:
        A string containing the CSV data.
    """
    flat_params = _flatten_params(params, param_defs)
    
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Parameter Name", "Expression", "Comment"])
    
    # Write data
    for name, value, comment in flat_params:
        # Fusion 360 doesn't like bools, convert to 0/1
        if isinstance(value, bool):
            value = 1 if value else 0
        
        # Handle empty description separately to avoid "Unit: " prefix
        if name == 'description' and not value:
            writer.writerow([name, "", ""])
        else:
            writer.writerow([name, value, comment])
        
    return output.getvalue().replace('\r', '')

if __name__ == '__main__':
    # Example usage for direct testing
    from ..schema import ElectricalParams, WindingParams, MagnetParams, GeometricParams, ThermalParams, DriverParams, GearParams, SimulationParams
    from ..ui import constants as C_UI # C_UI を再度インポート

    test_params = MotorParams(
        name="TestCSV",
        description="Test CSV Export",
        motor_type="outer_rotor",
        electrical=ElectricalParams(kv=120.0),
        winding=WindingParams(phase_resistance=0.2, phase_inductance=150.0, wiring_type='delta', continuous_current=12.0, peak_current=35.0, wire_diameter=0.6, turns_per_coil=40),
        magnets=MagnetParams(pole_pairs=14, use_halbach_array=True, magnet_width=8.0, magnet_thickness=2.5, magnet_length=15.0, remanence_br=1.25),
        geometry=GeometricParams(motor_outer_diameter=70.0, motor_inner_diameter=40.0, motor_length=30.0, slot_number=24),
        thermal=ThermalParams(ambient_temperature=30.0, thermal_resistance=1.5),
        driver=DriverParams(driver_on_resistance=0.004, driver_fixed_loss=2.5),
        gear=GearParams(gear_ratio=1.0, gear_efficiency=1.0),
        simulation=SimulationParams(bus_voltage=24.0)
    )

    csv_string = export_params_to_fusion_csv(test_params, C_UI.Layout.PARAM_DEFS) # param_defs を渡す
    print(csv_string)
    
    # Verify a few lines
    assert "Parameter Name,Expression,Comment" in csv_string
    assert "name,TestCSV" in csv_string
    assert "magnets_use_halbach_array,1" in csv_string # bool -> int
    assert "winding_wire_diameter,0.6" in csv_string
