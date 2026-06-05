"""Lightweight translation system – no external dependencies."""

_current_lang: str = "pl"


def set_language(lang: str) -> None:
    global _current_lang
    _current_lang = lang if lang in ("pl", "en") else "pl"


def current_language() -> str:
    return _current_lang


def tr(key: str) -> str:
    """Return the translated string for *key* in the current language.

    Falls back to the Polish string, then to the key itself if not found.
    """
    if _current_lang == "en":
        from i18n.en import STRINGS
    else:
        from i18n.pl import STRINGS
    if key in STRINGS:
        return STRINGS[key]
    # Fallback to Polish
    from i18n.pl import STRINGS as PL
    return PL.get(key, key)
