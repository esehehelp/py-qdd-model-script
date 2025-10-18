import numpy as np
from py_qdd_model.models.copper_loss import CopperLossModel
from py_qdd_model.models.iron_loss import IronLossModel
from py_qdd_model.schema import MotorParams
from py_qdd_model.models.motor_model import MotorModel


def test_copper_star():
    m = CopperLossModel('star')
    assert np.isclose(m.calculate_loss(10, 0.1), 3 * 100 * 0.1)


def test_iron_loss():
    m = IronLossModel(0.001, 1e-7)
    val = m.calculate_loss(np.array([1000.0]))
    assert val.shape == (1,)


def test_motor_analyze_shapes():
    params = MotorParams(kv=100.0, phase_resistance=0.1, phase_inductance=1e-4, pole_pairs=7, wiring_type='star', continuous_current=10.0, peak_current=30.0)
    model = MotorModel(params)
    I = np.linspace(0.1, 30.0, 5)
    RPM = np.linspace(100, 1000, 5)
    Ig, Rg = np.meshgrid(I, RPM)
    res = model.analyze(Ig, Rg)
    assert 'efficiency' in res and res['efficiency'].shape == Ig.shape
