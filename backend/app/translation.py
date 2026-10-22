"""Language registry and JSON-backed UI translations for AgriAid."""
import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)
TRANSLATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "translations"))
LANGS = {
    "english": ("en", "en"), "hindi": ("hi", "hi"), "telugu": ("te", "te"),
    "tamil": ("ta", "ta"), "kannada": ("kn", "kn"), "punjabi": ("pa", "pa"),
    "bengali": ("bn", "bn"), "gu": ("gu", "gu"),
}

class TranslationError(RuntimeError):
    pass

def language_payload(lang):
    """
    Return the selected language's JSON translations
    in the format expected by main.py.
    """
    if lang not in LANGS:
        raise ValueError(f"Unsupported language: {lang}")

    data = load_language(lang)

    return {
        "language_name": data.get("language_name", lang),
        "strings": data.get("strings", {}),
        "translation_complete": True
    }

@lru_cache(maxsize=8)
def load_language(lang):
    if lang not in LANGS:
        raise ValueError(f"Unsupported language: {lang}")
    path = os.path.join(TRANSLATIONS_DIR, f"{lang}.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise TranslationError(f"Could not load translation file {lang}.json: {exc}") from exc
    if not isinstance(data.get("strings"), dict):
        raise TranslationError(f"Translation file {lang}.json has no strings object")
    return data

def load_translations():
    return {lang: load_language(lang) for lang in LANGS}

def language_list():
    return [{"code": lang, "name": load_language(lang)["language_name"]} for lang in LANGS]

def ui_strings(lang):
    return load_language(lang)["strings"]

def language_name(lang):
    return load_language(lang)["language_name"]

def tr_code(lang):
    if lang not in LANGS:
        raise ValueError(f"Unsupported language: {lang}")
    return LANGS[lang][0]

def tts_code(lang):
    return LANGS.get(lang, ("en", "en"))[1]

def translated_labels(lang):
    strings = ui_strings(lang)
    return {key: strings[key] for key in ("diagnosis", "remedies", "prevention", "confidence", "contagion")}

# Kept for compatibility with any older code path. User descriptions are sent to Gemini
# directly now, so this does not make an external translation request.
def translate_to_english(text):
    return (text or "").strip()

def translate_batch(items, lang):
    """Compatibility shim: Gemini generates diagnosis text in the requested language."""
    if lang != "english":
        raise TranslationError("Text translation is handled by the language-specific Gemini prompt.")
    return list(items), True
