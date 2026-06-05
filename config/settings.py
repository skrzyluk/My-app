from PyQt6.QtCore import QSettings


class AppSettings:
    """Thin wrapper around QSettings (Windows registry).

    Stores app-level preferences that must survive across DB resets and are
    needed before the database is opened (e.g. theme on startup).
    """

    _ORG = "skrzyluk"
    _APP = "YouTubeNotifier"

    def __init__(self, _q: QSettings | None = None):
        self._q = _q or QSettings(self._ORG, self._APP)

    def get(self, key: str, default: str | None = None) -> str | None:
        value = self._q.value(key, default)
        return str(value) if value is not None else default

    def set(self, key: str, value: str) -> None:
        self._q.setValue(key, value)

    # ------------------------------------------------------------------ #
    # Typed helpers                                                       #
    # ------------------------------------------------------------------ #

    def language(self) -> str:
        return self.get("language", "pl") or "pl"

    def theme(self) -> str:
        return self.get("theme", "system") or "system"

    def notifications_enabled(self) -> bool:
        return self.get("notifications", "true") == "true"

    def set_language(self, lang: str) -> None:
        self.set("language", lang)

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    def set_notifications_enabled(self, enabled: bool) -> None:
        self.set("notifications", "true" if enabled else "false")
