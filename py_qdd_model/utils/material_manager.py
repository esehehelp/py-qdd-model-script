import json
from pathlib import Path
from typing import Dict, Any, Type, Optional, List
from functools import lru_cache

# Assuming these Pydantic models are defined in schema.py or a dedicated material_schema.py
# For now, we'll use a generic Dict[str, Any] for loaded material data.
# In a later step, we would validate these against specific Pydantic models.

class MaterialManager:
    _instance: Optional['MaterialManager'] = None
    _materials: Dict[str, Dict[str, Any]] = {}
    _base_path: Path = Path(__file__).parent.parent.parent / "parameters"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MaterialManager, cls).__new__(cls)
            cls._instance._load_all_materials()
        return cls._instance

    def _load_all_materials(self):
        """Scans the parameters directory and loads all material JSON files."""
        self._materials = {
            "core_materials": self._load_materials_from_dir("core_materials"),
            "magnet_materials": self._load_materials_from_dir("magnet_materials"),
            "wire_materials": self._load_materials_from_dir("wire_materials"),
        }
        print(f"MaterialManager loaded: {len(self._materials['core_materials'])} core, "
              f"{len(self._materials['magnet_materials'])} magnet, "
              f"{len(self._materials['wire_materials'])} wire materials.")

    def _load_materials_from_dir(self, sub_dir: str) -> Dict[str, Any]:
        """Loads JSON files from a specified subdirectory."""
        materials_dict = {}
        dir_path = self._base_path / sub_dir
        if not dir_path.exists():
            print(f"Warning: Material directory '{dir_path}' not found.")
            return materials_dict

        for file_path in dir_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "name" in data:
                        materials_dict[data["name"]] = data
                    else:
                        print(f"Warning: Material file '{file_path.name}' has no 'name' field. Skipping.")
            except json.JSONDecodeError as e:
                print(f"Error loading material file '{file_path.name}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred loading '{file_path.name}': {e}")
        return materials_dict

    @lru_cache(maxsize=None) # Cache material lookups
    def get_material(self, material_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific material by type and name."""
        return self._materials.get(material_type, {}).get(name)

    def get_available_materials(self, material_type: str) -> List[str]:
        """Returns a list of names of available materials for a given type."""
        return list(self._materials.get(material_type, {}).keys())

# Create a global instance for easy access
material_manager = MaterialManager()
