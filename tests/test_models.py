import numpy as np
import pytest
from py_qdd_model.models.copper_loss import CopperLossModel
from py_qdd_model.models.iron_loss import IronLossModel
from py_qdd_model.schema import MotorParams, ElectricalParams, WindingParams, MagnetParams, GeometricParams, ThermalParams, DriverParams, GearParams, SimulationParams
from py_qdd_model.models.motor_model import MotorModel
from py_qdd_model import constants as C

def test_copper_star():
    m = CopperLossModel('star')
    assert np.isclose(m.calculate_loss(10, 0.1), 3 * 100 * 0.1)

def test_iron_loss():
    import numpy as np
    m = IronLossModel(0.001, 1e-7, pole_pairs=7)
    rpm = np.array([1000.0])
    Bmax = np.array([0.3])
    val = m.calculate_loss(rpm, Bmax)
    assert val.shape == (1,)
    assert np.all(val > 0)

@pytest.fixture
def default_model():
    """Provides a default MotorModel instance for testing."""
    params = MotorParams(
        name="Test Motor",
        description="Motor for testing purposes",
        motor_type="inner_rotor",
        electrical=ElectricalParams(
            kv=100.0,
        ),
        winding=WindingParams(
            phase_resistance=0.1,
            phase_inductance=100.0,  # uH
            wiring_type='star',
            continuous_current=15.0,
            peak_current=30.0,
            wire_diameter=0.5,
            turns_per_coil=50,
        ),
        magnets=MagnetParams(
            pole_pairs=7,
            use_halbach_array=False,
            magnet_width=10,
            magnet_thickness=3,
            magnet_length=20,
            remanence_br=1.2,
        ),
        geometry=GeometricParams(
            motor_outer_diameter=60,
            motor_inner_diameter=30,
            motor_length=25,
            slot_number=12,
        ),
        thermal=ThermalParams(
            thermal_resistance=2.0,  # °C/W
            ambient_temperature=25.0,
        ),
        driver=DriverParams(
            driver_on_resistance=0.005,
            driver_fixed_loss=2.0,
        ),
        gear=GearParams(
            gear_ratio=9.0,
            gear_efficiency=0.95,
        ),
        simulation=SimulationParams(
            bus_voltage=48.0,
        )
    )
    # The MotorModel __init__ is responsible for converting uH to H for internal use
    return MotorModel(params)

def test_motor_analyze_shapes(default_model):
    model = default_model
    I = np.linspace(0.1, model.p.winding.peak_current, 5)
    RPM = np.linspace(100, 1000, 5)
    Ig, Rg = np.meshgrid(I, RPM)
    res = model.analyze(Ig, Rg)
    assert 'efficiency' in res and res['efficiency'].shape == Ig.shape

def test_temperature_convergence(default_model):
    model = default_model
    I = np.linspace(0.1, model.p.winding.peak_current, 5)
    RPM = np.linspace(100, 1000, 5)
    Ig, Rg = np.meshgrid(I, RPM)
    res = model.analyze(Ig, Rg, iters=100, relax=0.3)
    assert 'motor_temp' in res
    assert np.all(np.isfinite(res['motor_temp']))
    assert np.nanmin(res['motor_temp']) >= model.p.thermal.ambient_temperature - 1e-3

def test_thermal_convergence_high_current(default_model):
    """Tests if temperature rises significantly under high load."""
    model = default_model
    # Analyze a single high-current, but low-RPM point to avoid voltage limit
    current = np.array([[model.p.winding.peak_current * 0.9]])
    rpm = np.array([[300.0]]) # Shaft RPM
    res = model.analyze(current, rpm)
    final_temp = res['motor_temp'][0, 0]
    # Assert that the temperature has risen by a plausible amount (e.g., > 10°C)
    assert final_temp > model.p.thermal.ambient_temperature + 10.0

def test_voltage_limit_boundary(default_model):
    """Tests if the calculated voltage correctly reflects the voltage limit."""
    model = default_model
    # Ke in V/(rad/s) for star wiring is kt * sqrt(3)
    ke_line = model.ke * np.sqrt(3)
    
    # Find MOTOR RPM where back-EMF alone would exceed bus voltage
    rpm_limit_motor = model.p.simulation.bus_voltage / ke_line * C.PhysicsConstants.RAD_PER_SEC_TO_RPM
    
    # Convert to SHAFT RPM limit
    rpm_limit_shaft = rpm_limit_motor / model.p.gear.gear_ratio

    # Test a point expected to be OVER the voltage limit
    rpm_over = np.array([[rpm_limit_shaft * 1.1]])
    current_low = np.array([[1.0]]) # Low current to minimize resistive drop
    res_over = model.analyze(current_low, rpm_over)
    assert res_over['voltage'][0, 0] > model.p.simulation.bus_voltage

    # Test a point expected to be UNDER the voltage limit
    rpm_under = np.array([[rpm_limit_shaft * 0.9]])
    res_under = model.analyze(current_low, rpm_under)
    assert res_under['voltage'][0, 0] < model.p.simulation.bus_voltage

def test_efficiency_peak_location(default_model):
    """Tests for a plausible peak efficiency location."""
    model = default_model
    
    # --- Calculate a realistic RPM range based on voltage limit ---
    ke_line = model.ke * np.sqrt(3)
    rpm_limit_motor = model.p.simulation.bus_voltage / ke_line * C.PhysicsConstants.RAD_PER_SEC_TO_RPM
    rpm_limit_shaft = rpm_limit_motor / model.p.gear.gear_ratio
    
    # Use a range that covers the likely peak efficiency area
    I = np.linspace(1.0, model.p.winding.peak_current, 20)
    RPM = np.linspace(100, rpm_limit_shaft * 1.2, 20) # Use realistic RPM range
    Ig, Rg = np.meshgrid(I, RPM)
    
    res = model.analyze(Ig, Rg)
    
    # Mask out areas over the voltage limit, as they are not valid operating points
    valid_mask = res['voltage'] <= model.p.simulation.bus_voltage
    efficiency = np.where(valid_mask, res['efficiency'], 0)
    
    # Find peak efficiency
    max_eff = np.max(efficiency)
    peak_idx = np.unravel_index(np.argmax(efficiency), efficiency.shape)
    
    # Assert that peak efficiency is a reasonable value
    assert 0.5 < max_eff < 0.99
    
    # Assert that the peak is not at the lowest current or RPM
    # peak_idx[0] is the index for RPM, peak_idx[1] is for Current
    assert peak_idx[0] > 0  # Not at the lowest RPM
    assert peak_idx[1] > 0  # Not at the lowest Current

def test_motor_model_inductance_conversion():
    """Tests that the model correctly converts inductance from uH to H on initialization."""
    params_in_uh = MotorParams(
        name="Inductance Test Motor",
        motor_type="inner_rotor",
        electrical=ElectricalParams(kv=100.0),
        winding=WindingParams(
            phase_resistance=0.1,
            continuous_current=10.0,
            peak_current=30.0,
            phase_inductance=150.0,  # The value being tested (uH)
            wire_diameter=0.5,
            turns_per_coil=50,
        ),
        magnets=MagnetParams(
            pole_pairs=7,
            use_halbach_array=False,
            magnet_width=10,
            magnet_thickness=3,
            magnet_length=20,
            remanence_br=1.2,
        ),
        geometry=GeometricParams(
            motor_outer_diameter=60,
            motor_inner_diameter=30,
            motor_length=25,
            slot_number=12,
        ),
        thermal=ThermalParams(),
        driver=DriverParams(),
        gear=GearParams(),
        simulation=SimulationParams(),
    )
    
    model = MotorModel(params_in_uh)
    
    expected_h = 150e-6
    assert model.p.winding.phase_inductance == pytest.approx(expected_h)
