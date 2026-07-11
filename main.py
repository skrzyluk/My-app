import sys
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Notifier")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("skrzyluk")
    app.setQuitOnLastWindowClosed(False)

    # Apply saved theme and language before any window opens
    from config.settings import AppSettings
    from config.theme import apply_theme
    import i18n

    s = AppSettings()
    i18n.set_language(s.language())
    apply_theme(app, s.theme(), white_text=s.white_text(), font_scale=s.font_size())

    window = LoginWindow()
    window.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
