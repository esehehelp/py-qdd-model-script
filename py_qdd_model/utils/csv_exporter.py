import csv
import io
from ..schema import MotorParams
# from ..ui import constants as C_UI # 削除
# from ..i18n.translator import t # 削除

def _flatten_params(params: MotorParams, param_defs: dict): # param_defs を引数に戻す
    """
    Flattens the nested Pydantic model into a list of tuples for CSV export.
    (parameter_name, value, unit)
    """
    flat_list = []
    
    # param_defs から直接ラベルを取得する
    param_labels = {}
    for group_key, group_fields in param_defs.items():
        # group_key が翻訳キーの場合とそうでない場合があるため、t() を使う
        # ただし、C_UI.Layout.PARAM_DEFS の構造上、group_key は文字列リテラルか t() の結果
        # ここでは、group_fields の中の各keyに対応するラベルを取得する
        for key, (label, default_value, *_) in group_fields.items():
            param_labels[key] = label

    def recurse(model_part, prefix=""):
        for field_name, value in model_part:
            if isinstance(value, (int, float, str, bool)):
                param_name = f"{prefix}{field_name}"
                unit = param_labels.get(field_name, "") # ラベル全体を単位として使用
                flat_list.append((param_name, value, unit))
            elif hasattr(value, 'model_dump'): # It's a nested Pydantic model
                recurse(value, prefix=f"{field_name}_")

    recurse(params)
    return flat_list

def export_params_to_fusion_csv(params: MotorParams, param_defs: dict) -> str: # param_defs を引数に戻す
    """
    Exports motor parameters to a CSV string compatible with Fusion 360.
    
    Args:
        params: The MotorParams object.
        param_defs: The UI parameter definitions for unit lookup.

    Returns:
        A string containing the CSV data.
    """
    flat_params = _flatten_params(params, param_defs) # param_defs を渡す
    
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Parameter Name", "Expression", "Comment"])
    
    # Write data
    for name, value, unit in flat_params:
        # Fusion 360 doesn't like bools, convert to 0/1
        if isinstance(value, bool):
            value = 1 if value else 0
        
        # We don't have units for all params, so the comment may be empty
        comment = f"Unit: {unit}" if unit else ""
        writer.writerow([name, value, comment])
        
    return output.getvalue().replace('\r', '') # \r を削除

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
