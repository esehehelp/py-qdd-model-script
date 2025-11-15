import json
import numpy as np
from py_qdd_model.schema import MotorParams
from py_qdd_model.models.motor_model import MotorModel
from py_qdd_model.utils.io import save_json

def run_from_preset(preset_path: str, out_json: str = 'results.json'):
    with open(preset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    params = MotorParams(**data)
    model = MotorModel(params)
    current_range = np.linspace(0.1, params.winding.peak_current, 50)
    # estimate theoretical max rpm similarly as GUI
    if params.winding.wiring_type == 'star':
        ke_line = model.ke * np.sqrt(3)
    else:
        ke_line = model.ke
    if ke_line > 0:
        motor_rpm_unloaded = params.simulation.bus_voltage / ke_line * (60 / (2 * 3.141592653589793))
        theoretical_max_rpm = motor_rpm_unloaded / params.gear.gear_ratio
    else:
        theoretical_max_rpm = 5000
    rpm_range = np.linspace(0.1, theoretical_max_rpm * 1.1, 50)
    I, RPM = np.meshgrid(current_range, rpm_range)
    res = model.analyze(I, RPM)
    # serialize numeric arrays to lists
    serial = {k: np.asarray(v).tolist() for k, v in res.items()}
    save_json(out_json, {'params': data, 'results': serial})
    print(f"Saved results to {out_json}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('preset', help='JSON preset file path')
    parser.add_argument('--out', default='results.json', help='output JSON path')
    args = parser.parse_args()
    run_from_preset(args.preset, args.out)
