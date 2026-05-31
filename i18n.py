import json
import os
from typing import Dict

DEFAULT_LANG = "en"
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

def load_locale(lang_code: str) -> Dict[str, str]:
    """Load translation JSON for the given language.
    Falls back to DEFAULT_LANG if file missing or load fails.
    """
    path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if not os.path.isfile(path):
        path = os.path.join(LOCALES_DIR, f"{DEFAULT_LANG}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_current_locale = load_locale(DEFAULT_LANG)

def set_locale(lang_code: str):
    global _current_locale
    _current_locale = load_locale(lang_code)

def t(key: str) -> str:
    """Translate a key using the currently loaded locale.
    If the key is missing, return the key itself.
    """
    return _current_locale.get(key, key)
