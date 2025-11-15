import pytest
from pathlib import Path
import tempfile
import os

from py_qdd_model.schema import MotorParams, ElectricalParams, WindingParams, MagnetParams, GeometricParams, ThermalParams, DriverParams, GearParams, SimulationParams, MotorType
from py_qdd_model.three_d.model_generator import generate_motor_model

@pytest.fixture
def temp_output_dir():
    """Provides a temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def base_motor_params():
    """Provides a base MotorParams instance for testing."""
    return MotorParams(
        name="TestMotor",
        description="A motor for 3D model testing",
        motor_type=MotorType.INNER_ROTOR, # Default to inner rotor
        electrical=ElectricalParams(kv=100.0),
        winding=WindingParams(phase_resistance=0.1, phase_inductance=100.0, wiring_type='star', continuous_current=10.0, peak_current=30.0, wire_diameter=0.5, turns_per_coil=50),
        magnets=MagnetParams(pole_pairs=7, use_halbach_array=False, magnet_width=10.0, magnet_thickness=3.0, magnet_length=20.0, remanence_br=1.2),
        geometry=GeometricParams(
            motor_outer_diameter=60.0, 
            motor_inner_diameter=30.0, 
            motor_length=25.0, 
            slot_number=12,
            slot_depth=8.0,
            slot_top_width=2.5,
            slot_bottom_width=5.0
        ),
        thermal=ThermalParams(ambient_temperature=25.0, thermal_resistance=2.0),
        driver=DriverParams(driver_on_resistance=0.005, driver_fixed_loss=2.0),
        gear=GearParams(gear_ratio=9.0, gear_efficiency=0.95),
        simulation=SimulationParams(bus_voltage=48.0)
    )

def test_generate_inner_rotor_model(temp_output_dir, base_motor_params):
    """Test generation of an inner rotor motor model."""
    params = base_motor_params.model_copy(deep=True)
    params.motor_type = MotorType.INNER_ROTOR
    
    output_path = generate_motor_model(params, temp_output_dir)
    
    assert output_path.exists()
    assert output_path.suffix == ".step"
    assert output_path.name == "TestMotor_model.step"
    assert output_path.stat().st_size > 0 # Check if file is not empty

def test_generate_outer_rotor_model(temp_output_dir, base_motor_params):
    """Test generation of an outer rotor motor model."""
    params = base_motor_params.model_copy(deep=True)
    params.motor_type = MotorType.OUTER_ROTOR
    
    output_path = generate_motor_model(params, temp_output_dir)
    
    assert output_path.exists()
    assert output_path.suffix == ".step"
    assert output_path.name == "TestMotor_model.step"
    assert output_path.stat().st_size > 0

def test_generate_axial_flux_model(temp_output_dir, base_motor_params):
    """Test generation of an axial flux motor model."""
    params = base_motor_params.model_copy(deep=True)
    params.motor_type = MotorType.AXIAL_FLUX
    
    output_path = generate_motor_model(params, temp_output_dir)
    
    assert output_path.exists()
    assert output_path.suffix == ".step"
    assert output_path.name == "TestMotor_model.step"
    assert output_path.stat().st_size > 0

def test_generate_model_invalid_params(temp_output_dir, base_motor_params):
    """Test generation with invalid parameters (e.g., zero length)."""
    params = base_motor_params.model_copy(deep=True)
    params.geometry.motor_length = 0.0 # Invalid length
    
    # Expecting an error from cadquery or pydantic validation
    # For now, just ensure it doesn't crash and potentially creates an empty file or raises an error
    # A more robust test would check for specific error types if expected.
    with pytest.raises(Exception): # CadQuery might raise an exception for invalid geometry
        generate_motor_model(params, temp_output_dir)
