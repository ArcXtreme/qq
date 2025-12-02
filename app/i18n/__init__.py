import json
import os

_i18n_cache = {}

def load_lang(lang_code: str):
    if not lang_code:
        lang_code = "en"
    lang_code = lang_code.lower()
    if lang_code in _i18n_cache:
        return _i18n_cache[lang_code]
    path = os.path.join(os.path.dirname(__file__), f"{lang_code}.json")
    if not os.path.exists(path):
        # fallback to English
        path = os.path.join(os.path.dirname(__file__), "en.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _i18n_cache[lang_code] = data
    return data

def translate(key: str, lang: str = "en", params: dict = None) -> str:
    d = load_lang(lang)
    text = d.get(key) or load_lang("en").get(key) or key
    if params:
        try:
            text = text.format(**params)
        except Exception:
            # safe fallback
            pass
    return text
