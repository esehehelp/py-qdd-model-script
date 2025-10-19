import pytest
from py_qdd_model.models import winding_model

# --- Test Data ---

@pytest.fixture
def reference_params():
    """Returns a copy of the built-in medium profile."""
    return winding_model.BUILTIN_PROFILES["medium"].copy()

@pytest.fixture
def target_params():
    """Returns a sample target parameter set."""
    return {
        "kv": 200.0, # Different from medium profile
        "peak_current": 40.0
    }

# --- Test Cases ---

def test_calculation_with_valid_inputs(target_params, reference_params):
    """Tests that the calculation runs successfully with valid inputs."""
    density = 8.0
    result = winding_model.estimate_new_winding(target_params, reference_params, density)

    assert isinstance(result, dict)
    expected_keys = ["diameter_mm", "length", "resistance", "inductance"]
    for key in expected_keys:
        assert key in result
        assert isinstance(result[key], float)
        assert result[key] > 0

def test_missing_target_keys(reference_params):
    """Tests that a KeyError is raised if target params are missing keys."""
    with pytest.raises(KeyError, match="Target data is missing required key: 'kv'"):
        winding_model.estimate_new_winding({}, reference_params, 8.0)
    
    with pytest.raises(KeyError, match="Target data is missing required key: 'peak_current'"):
        winding_model.estimate_new_winding({"kv": 100.0}, reference_params, 8.0)

def test_missing_reference_keys(target_params):
    """Tests that a KeyError is raised if reference params are missing keys."""
    with pytest.raises(KeyError, match="Reference data is missing required key: 'phase_resistance'"):
        winding_model.estimate_new_winding(target_params, {"kv": 1.0, "peak_current": 1.0, "phase_inductance": 1.0}, 8.0)

def test_turn_ratio_logic(reference_params):
    """Tests the core scaling logic of the model."""
    # Target KV is half of reference, so turn_ratio should be 2
    target = {
        "kv": reference_params["kv"] / 2.0,
        "peak_current": reference_params["peak_current"] # Keep same current for simplicity
    }
    density = 10.0

    result = winding_model.estimate_new_winding(target, reference_params, density)

    # Inductance should be turn_ratio^2 (2^2=4) times the reference
    expected_inductance = reference_params["phase_inductance"] * 4.0
    assert pytest.approx(result["inductance"], rel=1e-9) == expected_inductance
