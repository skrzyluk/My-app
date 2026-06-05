from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply *theme* ('system' | 'light' | 'dark') to the running application."""
    if theme == "dark":
        app.setStyle("Fusion")
        app.setPalette(_dark_palette())
    elif theme == "light":
        app.setStyle("Fusion")
        app.setPalette(_light_palette())
    else:
        app.setStyle("")
        app.setPalette(QPalette())


def _light_palette() -> QPalette:
    p = QPalette()
    light     = QColor(240, 240, 240)
    white     = QColor(255, 255, 255)
    black     = QColor(0,   0,   0)
    highlight = QColor(42,  130, 218)

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
    dark   = QColor(53,  53,  53)
    darker = QColor(35,  35,  35)
    white  = QColor(255, 255, 255)
    blue   = QColor(42,  130, 218)

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
    p.setColor(QPalette.ColorRole.Link,            blue)
    p.setColor(QPalette.ColorRole.Highlight,       blue)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    return p
