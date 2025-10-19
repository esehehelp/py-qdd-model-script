import tomllib
from typing import Dict, Any

DEFAULT_SETTINGS = {
    "window": {
        "initial_size": "1280x900",
    },
    "layout": {
        "main_padding": 10,
        "widget_pady": 8,
        "button_padx": 4,
        "combobox_width": 20,
    },
    "plot": {
        "figure_size_x": 8,
        "figure_size_y": 8,
        "display_dpi": 100,
        "save_dpi": 300,
        "downsample_factor": 3
    },
    "analysis": {
        "grid_points": 50,
        "rpm_safety_margin": 1.1,
    },
    "language": {
        "lang": "jp"
    }
}

def load_settings(path: str = "settings.toml") -> Dict[str, Any]:
    """
    Loads settings from a TOML file, providing default values for missing keys.
    """
    settings = DEFAULT_SETTINGS.copy()
    try:
        with open(path, "rb") as f:
            user_settings = tomllib.load(f)
            for section, keys in user_settings.items():
                if section in settings:
                    settings[section].update(keys)
                else:
                    settings[section] = keys
    except FileNotFoundError:
        # File doesn't exist, use default settings
        pass
    except tomllib.TOMLDecodeError as e:
        print(f"Warning: Could not parse settings.toml. Using default settings. Error: {e}")

    return settings

# Create a single instance to be imported by other modules
settings = load_settings()
