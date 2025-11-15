import json
import pathlib
import functools
from typing import Dict, Any
from ..utils.config import settings

class Translator:
    def __init__(self, lang: str):
        self.lang = lang
        self.data = self._load_language_data(lang)

    def _load_language_data(self, lang_code: str) -> Dict[str, Any]:
        """Loads the specified language JSON file, with a fallback to English."""
        i18n_dir = pathlib.Path(__file__).parent.resolve()
        lang_file = i18n_dir / f"{lang_code}.json"

        if not lang_file.exists():
            print(f"Warning: Language file '{lang_file}' not found. Falling back to 'en'.")
            lang_file = i18n_dir / "en.json"
            if not lang_file.exists():
                # This is a critical error, as the base language is missing.
                raise FileNotFoundError("Default language file 'en.json' is missing.")

        with open(lang_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get(self, key: str, default: str = "") -> Any:
        """Retrieves a value from the nested language data using a dot-separated key."""
        try:
            return functools.reduce(lambda d, k: d[k], key.split('.'), self.data)
        except (KeyError, TypeError):
            return default or key

# Create a singleton instance of the translator
_translator = Translator(settings.language.lang)

# Global translation function
def t(key: str, default: str = "") -> Any:
    """A convenient global function to access the translator."""
    return _translator.get(key, default=default)

def set_language(lang_code: str):
    """Sets the global translator to a new language."""
    global _translator
    _translator = Translator(lang_code)
