from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply *theme* ('system' | 'light' | 'dark') to the running application."""
    from resources.styles import LIGHT_QSS, DARK_QSS
    if theme == "dark":
        app.setStyle("Fusion")
        app.setPalette(_dark_palette())
        app.setStyleSheet(DARK_QSS)
    elif theme == "light":
        app.setStyle("Fusion")
        app.setPalette(_light_palette())
        app.setStyleSheet(LIGHT_QSS)
    else:
        app.setStyle("")
        app.setPalette(QPalette())
        app.setStyleSheet("")


def _light_palette() -> QPalette:
    p = QPalette()
    light     = QColor(245, 245, 245)
    white     = QColor(255, 255, 255)
    black     = QColor(33,  33,  33)
    highlight = QColor(229, 57,  53)

    p.setColor(QPalette.ColorRole.Window,          light)
    p.setColor(QPalette.ColorRole.WindowText,      black)
    p.setColor(QPalette.ColorRole.Base,            white)
    p.setColor(QPalette.ColorRole.AlternateBase,   light)
    p.setColor(QPalette.ColorRole.Text,            black)
    p.setColor(QPalette.ColorRole.Button,          light)
    p.setColor(QPalette.ColorRole.ButtonText,      black)
    p.setColor(QPalette.ColorRole.Highlight,       highlight)
    p.setColor(QPalette.ColorRole.HighlightedText, white)
    return p


def _dark_palette() -> QPalette:
    p = QPalette()
    dark   = QColor(30,  30,  30)
    darker = QColor(18,  18,  18)
    white  = QColor(232, 234, 237)
    red    = QColor(239, 83,  80)

    p.setColor(QPalette.ColorRole.Window,          dark)
    p.setColor(QPalette.ColorRole.WindowText,      white)
    p.setColor(QPalette.ColorRole.Base,            darker)
    p.setColor(QPalette.ColorRole.AlternateBase,   dark)
    p.setColor(QPalette.ColorRole.ToolTipBase,     dark)
    p.setColor(QPalette.ColorRole.ToolTipText,     white)
    p.setColor(QPalette.ColorRole.Text,            white)
    p.setColor(QPalette.ColorRole.Button,          dark)
    p.setColor(QPalette.ColorRole.ButtonText,      white)
    p.setColor(QPalette.ColorRole.BrightText,      QColor(255, 0, 0))
    p.setColor(QPalette.ColorRole.Link,            red)
    p.setColor(QPalette.ColorRole.Highlight,       red)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    return p
