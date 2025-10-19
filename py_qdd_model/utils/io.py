import json
from typing import Any
from ..exceptions import FileOperationError

def save_json(filepath: str, data: Any):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except (IOError, TypeError) as e:
        raise FileOperationError(f"Failed to save JSON to {filepath}: {e}") from e

def load_json(filepath: str) -> Any:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        raise FileOperationError(f"Failed to load JSON from {filepath}: {e}") from e

def save_text(filepath: str, content: str):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        raise FileOperationError(f"Failed to save text to {filepath}: {e}") from e
