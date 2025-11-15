import tomllib
from typing import Any, Dict
from ..schema import AppSettings
from pydantic import ValidationError

def _deep_merge(source: Dict, destination: Dict) -> Dict:
    """
    Recursively merges source dict into destination dict.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _deep_merge(value, node)
        else:
            destination[key] = value
    return destination

def load_settings(path: str = "settings.toml") -> AppSettings:
    """
    Loads settings from a TOML file, validates them against the AppSettings model,
    and returns a type-safe settings object.
    """
    # Start with default settings by creating a model instance
    default_settings_dict = AppSettings().model_dump()
    
    final_settings_dict = default_settings_dict

    try:
        with open(path, "rb") as f:
            user_settings = tomllib.load(f)
            # Merge user settings into the default settings
            final_settings_dict = _deep_merge(user_settings, default_settings_dict)

    except FileNotFoundError:
        # File doesn't exist, use default settings, which is already the case
        pass
    except tomllib.TOMLDecodeError as e:
        print(f"Warning: Could not parse '{path}'. Using default settings. Error: {e}")
        # Fallback to defaults
        final_settings_dict = AppSettings().model_dump()

    try:
        # Validate the final merged dictionary
        settings_obj = AppSettings.model_validate(final_settings_dict)
        return settings_obj
    except ValidationError as e:
        print(f"Warning: Settings validation failed. Using default settings. Error: {e}")
        # On validation failure, return a default AppSettings instance
        return AppSettings()

# Create a single instance to be imported by other modules
settings = load_settings()
