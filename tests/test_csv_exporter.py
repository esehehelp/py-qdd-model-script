import pytest
import pytest
from py_qdd_model.schema import MotorParams, ElectricalParams, WindingParams, MagnetParams, GeometricParams, ThermalParams, DriverParams, GearParams, SimulationParams, MotorType
from py_qdd_model.utils.csv_exporter import export_params_to_fusion_csv
# from py_qdd_model.ui import constants as C_UI # For param_defs

@pytest.fixture
def english_param_defs():
    """Provides a simplified English param_defs for testing."""
    return {
        "general": {
            'name': ("name", "My Motor"),
            'description': ("description", "A custom motor model."),
            'motor_type': ("motor_type", 'inner_rotor', ['inner_rotor', 'outer_rotor', 'axial_flux']),
        },
        "electrical": {
            'kv': ("KV Rating [rpm/V]", 100.0),
            'hysteresis_coeff': ("Hysteresis Coefficient [W/rpm]", 0.001),
            'eddy_current_coeff': ("Eddy Current Coefficient [W/rpm^2]", 1e-7),
        },
        "winding": {
            'phase_resistance': ("Phase Resistance (25°C) [Ohm]", 0.1),
            'phase_inductance': ("Phase Inductance [uH]", 100.0),
            'wiring_type': ("Wiring Type", 'star', ['star', 'delta']),
            'continuous_current': ("Continuous Current [A]", 10.0),
            'peak_current': ("Peak Current [A]", 30.0),
            'wire_diameter': ("Wire Diameter [mm]", 0.5),
            'turns_per_coil': ("Turns per Coil", 50),
        },
        "magnets": {
            'pole_pairs': ("Pole Pairs", 7),
            'use_halbach_array': ("Use Halbach Array", False),
            'magnet_width': ("Magnet Width [mm]", 10.0),
            'magnet_thickness': ("Magnet Thickness [mm]", 3.0),
            'magnet_length': ("Magnet Length [mm]", 20.0),
            'remanence_br': ("Remanence Br [T]", 1.2),
        },
        "geometry": {
            'motor_outer_diameter': ("Motor Outer Diameter [mm]", 60.0),
            'motor_inner_diameter': ("Motor Inner Diameter [mm]", 30.0),
            'motor_length': ("Motor Length [mm]", 25.0),
            'slot_number': ("Slot Number", 12),
            'slot_depth': ("Slot Depth [mm]", 5.0),
            'slot_top_width': ("Slot Top Width [mm]", 2.0),
            'slot_bottom_width': ("Slot Bottom Width [mm]", 4.0),
        },
        "thermal": {
            'ambient_temperature': ("Ambient Temperature [°C]", 25.0),
            'thermal_resistance': ("Thermal Resistance [°C/W]", 2.0),
        },
        "driver": {
            'driver_on_resistance': ("Driver ON-Resistance [Ohm]", 0.005),
            'driver_fixed_loss': ("Driver Fixed Loss [W]", 2.0),
        },
        "gear": {
            'gear_ratio': ("Gear Ratio", 9.0),
            'gear_efficiency': ("Gear Efficiency", 0.95),
        },
        "simulation": {
            'bus_voltage': ("Bus Voltage [V]", 48.0),
        }
    }

@pytest.fixture
def base_motor_params():
    """Provides a base MotorParams instance for testing."""
    return MotorParams(
        name="TestCSV",
        description="A motor for CSV export testing",
        motor_type=MotorType.INNER_ROTOR,
        electrical=ElectricalParams(kv=120.0),
        winding=WindingParams(phase_resistance=0.2, phase_inductance=150.0, wiring_type='delta', continuous_current=12.0, peak_current=35.0, wire_diameter=0.6, turns_per_coil=40),
        magnets=MagnetParams(pole_pairs=14, use_halbach_array=True, magnet_width=8.0, magnet_thickness=2.5, magnet_length=15.0, remanence_br=1.25),
        geometry=GeometricParams(
            motor_outer_diameter=70.0, 
            motor_inner_diameter=40.0,
            motor_length=30.0,
            slot_number=24,
            slot_depth=6.0,
            slot_top_width=2.0,
            slot_bottom_width=4.0
        ),
        thermal=ThermalParams(ambient_temperature=30.0, thermal_resistance=1.5),
        driver=DriverParams(driver_on_resistance=0.004, driver_fixed_loss=2.5),
        gear=GearParams(gear_ratio=1.0, gear_efficiency=1.0),
        simulation=SimulationParams(bus_voltage=24.0)
    )

def test_export_csv_header(base_motor_params, english_param_defs):
    """Test if the CSV header is correctly generated."""
    csv_string = export_params_to_fusion_csv(base_motor_params, english_param_defs)
    lines = csv_string.strip().split('\n')
    assert lines[0] == "Parameter Name,Expression,Comment"

def test_export_csv_content(base_motor_params, english_param_defs):
    """Test if key parameters are present and correctly formatted."""
    csv_string = export_params_to_fusion_csv(base_motor_params, english_param_defs)
    
    assert "name,TestCSV," in csv_string
    assert "motor_type,inner_rotor," in csv_string
    assert "electrical_kv,120.0," in csv_string
    assert "winding_phase_resistance,0.2," in csv_string
    assert "magnets_use_halbach_array,1," in csv_string # Boolean should be 1
    assert "geometry_slot_number,24," in csv_string
    assert "geometry_slot_depth,6.0," in csv_string
    assert "simulation_bus_voltage,24.0," in csv_string

def test_export_csv_units(base_motor_params, english_param_defs):
    """Test if units are correctly included in comments."""
    csv_string = export_params_to_fusion_csv(base_motor_params, english_param_defs)
    
    assert "electrical_kv,120.0,Unit: KV Rating [rpm/V]" in csv_string
    assert "winding_phase_resistance,0.2,Unit: Phase Resistance (25°C) [Ohm]" in csv_string
    assert "geometry_slot_depth,6.0,Unit: Slot Depth [mm]" in csv_string
    assert "simulation_bus_voltage,24.0,Unit: Bus Voltage [V]" in csv_string

def test_export_csv_empty_description(base_motor_params, english_param_defs):
    """Test with an empty description."""
    params = base_motor_params.model_copy(deep=True)
    params.description = ""
    csv_string = export_params_to_fusion_csv(params, english_param_defs)
    assert "description,," in csv_string # Empty description should result in empty expression and comment

def test_export_csv_edge_cases(base_motor_params):
    """Tests edge cases like missing keys in param_defs and malformed units."""
    # param_defs with some keys missing and some malformed labels
    partial_param_defs = {
        "electrical": {
            'kv': ("KV Rating [rpm/V]", 100.0),
            # hysteresis_coeff is missing
        },
        "winding": {
            'phase_resistance': ("Resistance Ohm", 0.1), # Unit not in brackets
            'phase_inductance': ("Inductance", 100.0),   # No unit
        },
    }

    csv_string = export_params_to_fusion_csv(base_motor_params, partial_param_defs)

    # Test for a key completely missing from param_defs
    # It should use the key name as the comment
    assert "electrical_hysteresis_coeff,0.001,Unit: electrical_hysteresis_coeff" in csv_string

    # Test for a label where the unit is not in brackets
    assert "winding_phase_resistance,0.2,Unit: Resistance Ohm" in csv_string

    # Test for a label with no unit
    assert "winding_phase_inductance,150.0,Unit: Inductance" in csv_string
