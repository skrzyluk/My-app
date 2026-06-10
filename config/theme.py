from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


def apply_theme(
    app: QApplication,
    theme: str,
    *,
    white_text: bool = False,
    font_scale: str = "normal",
) -> None:
    """Apply *theme* to the running application.

    *theme* may be ``"system"``, a legacy ``"light"``/``"dark"`` name, or one of
    the named themes in :data:`resources.styles.THEMES` (e.g. ``"dark-ocean"``).
    Anything unknown – including ``"system"`` – falls back to the native palette
    with no stylesheet, so the OS look-and-feel shows through.
    """
    from resources.styles import THEMES, LIGHT_THEMES, _THEME_ALIASES, build_qss

    if theme != "system" and (theme in THEMES or theme in _THEME_ALIASES):
        resolved = theme if theme in THEMES else _THEME_ALIASES[theme]
        app.setStyle("Fusion")
        is_light = resolved in LIGHT_THEMES
        app.setPalette(_palette_for(resolved, light=is_light))
        app.setStyleSheet(build_qss(resolved, white_text=white_text, font_scale=font_scale))
    else:
        app.setStyle("")
        app.setPalette(QPalette())
        app.setStyleSheet("")


def _palette_for(theme: str, *, light: bool) -> QPalette:
    """Build a QPalette from a theme's tokens (so accents/menus match the QSS)."""
    from resources.styles import THEMES

    t = THEMES[theme]
    bg        = QColor(t["bg_app"])
    surface   = QColor(t["bg_surface"])
    text      = QColor(t["text_primary"])
    secondary = QColor(t["text_secondary"])
    accent    = QColor(t["accent"])
    on_accent = QColor(t["text_on_accent"])

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          bg)
    p.setColor(QPalette.ColorRole.WindowText,      text)
    p.setColor(QPalette.ColorRole.Base,            bg)
    p.setColor(QPalette.ColorRole.AlternateBase,   surface)
    p.setColor(QPalette.ColorRole.ToolTipBase,     surface)
    p.setColor(QPalette.ColorRole.ToolTipText,     text)
    p.setColor(QPalette.ColorRole.Text,            text)
    p.setColor(QPalette.ColorRole.PlaceholderText, secondary)
    p.setColor(QPalette.ColorRole.Button,          surface)
    p.setColor(QPalette.ColorRole.ButtonText,      text)
    p.setColor(QPalette.ColorRole.BrightText,      accent)
    p.setColor(QPalette.ColorRole.Link,            accent)
    p.setColor(QPalette.ColorRole.Highlight,       accent)
    p.setColor(QPalette.ColorRole.HighlightedText, on_accent)
    return p


def _light_palette() -> QPalette:
    """Light palette (back-compat helper)."""
    return _palette_for("light-classic", light=True)


def _dark_palette() -> QPalette:
    """Dark palette (back-compat helper)."""
    return _palette_for("dark-crimson", light=False)
