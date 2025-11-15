import pytest
from py_qdd_model.utils.material_manager import MaterialManager
from pathlib import Path
import json

# Define a temporary directory for test materials
@pytest.fixture(scope="module")
def temp_material_dir(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("test_materials")
    
    # Create subdirectories
    core_dir = temp_dir / "core_materials"
    magnet_dir = temp_dir / "magnet_materials"
    wire_dir = temp_dir / "wire_materials"
    core_dir.mkdir()
    magnet_dir.mkdir()
    wire_dir.mkdir()

    # Create sample material files
    with open(core_dir / "TestCore.json", "w") as f:
        json.dump({"name": "TestCore", "density": 7650}, f)
    with open(magnet_dir / "TestMagnet.json", "w") as f:
        json.dump({"name": "TestMagnet", "remanence_br": 1.2}, f)
    with open(wire_dir / "TestWire.json", "w") as f:
        json.dump({"name": "TestWire", "diameter_bare": 0.5}, f)
    
    # Create a file with no name field
    with open(core_dir / "NoName.json", "w") as f:
        json.dump({"density": 1000}, f)

    # Create an invalid JSON file
    with open(core_dir / "Invalid.json", "w") as f:
        f.write("{invalid json}")

    return temp_dir

@pytest.fixture(scope="function")
def material_manager_instance(temp_material_dir):
    # Temporarily override the base_path for MaterialManager
    original_base_path = MaterialManager._base_path
    MaterialManager._base_path = temp_material_dir
    MaterialManager._instance = None # Reset singleton
    manager = MaterialManager()
    yield manager
    MaterialManager._base_path = original_base_path # Restore original path
    MaterialManager._instance = None # Reset singleton again

def test_material_manager_singleton(material_manager_instance):
    manager1 = material_manager_instance
    manager2 = MaterialManager()
    assert manager1 is manager2

def test_load_materials(material_manager_instance):
    manager = material_manager_instance
    assert "TestCore" in manager.get_available_materials("core_materials")
    assert "TestMagnet" in manager.get_available_materials("magnet_materials")
    assert "TestWire" in manager.get_available_materials("wire_materials")
    assert "NoName" not in manager.get_available_materials("core_materials") # Should be skipped due to no name

def test_get_material(material_manager_instance):
    manager = material_manager_instance
    core_material = manager.get_material("core_materials", "TestCore")
    assert core_material is not None
    assert core_material["name"] == "TestCore"
    assert core_material["density"] == 7650

    magnet_material = manager.get_material("magnet_materials", "TestMagnet")
    assert magnet_material is not None
    assert magnet_material["name"] == "TestMagnet"
    assert magnet_material["remanence_br"] == 1.2

    wire_material = manager.get_material("wire_materials", "TestWire")
    assert wire_material is not None
    assert wire_material["name"] == "TestWire"
    assert wire_material["diameter_bare"] == 0.5

    # Test non-existent material
    non_existent = manager.get_material("core_materials", "NonExistent")
    assert non_existent is None

def test_get_available_materials_non_existent_type(material_manager_instance):
    manager = material_manager_instance
    assert manager.get_available_materials("non_existent_type") == []

def test_material_manager_reloads_on_reset(temp_material_dir):
    # First instance
    MaterialManager._base_path = temp_material_dir
    MaterialManager._instance = None
    manager1 = MaterialManager()
    assert "TestCore" in manager1.get_available_materials("core_materials")

    # Add a new material
    with open(temp_material_dir / "core_materials" / "NewCore.json", "w") as f:
        json.dump({"name": "NewCore", "density": 8000}, f)
    
    # Second instance without reset should not see new material
    manager2 = MaterialManager()
    assert "NewCore" not in manager2.get_available_materials("core_materials")

    # Reset and create a third instance, which should see the new material
    MaterialManager._instance = None
    manager3 = MaterialManager()
    assert "NewCore" in manager3.get_available_materials("core_materials")
