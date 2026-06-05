import pytest
from PyQt6.QtGui import QPalette

from config.theme import apply_theme, _dark_palette


class TestDarkPalette:
    def test_window_is_dark(self):
        p = _dark_palette()
        assert p.color(QPalette.ColorRole.Window).lightness() < 128

    def test_window_text_is_light(self):
        p = _dark_palette()
        assert p.color(QPalette.ColorRole.WindowText).lightness() > 128

    def test_base_is_very_dark(self):
        p = _dark_palette()
        assert p.color(QPalette.ColorRole.Base).lightness() < 60

    def test_highlight_color_set(self):
        p = _dark_palette()
        h = p.color(QPalette.ColorRole.Highlight)
        assert h.isValid()
        assert h != p.color(QPalette.ColorRole.Window)


class TestApplyTheme:
    def test_dark_theme_darkens_window(self, qapp):
        apply_theme(qapp, "dark")
        palette = qapp.palette()
        assert palette.color(QPalette.ColorRole.Window).lightness() < 128

    def test_light_theme_lightens_window(self, qapp):
        apply_theme(qapp, "light")
        palette = qapp.palette()
        assert palette.color(QPalette.ColorRole.Window).lightness() > 128

    def test_system_theme_does_not_raise(self, qapp):
        apply_theme(qapp, "system")  # must not raise

    def test_unknown_theme_treated_as_system(self, qapp):
        apply_theme(qapp, "unknown_value")  # must not raise

    def test_dark_then_light_restores_light(self, qapp):
        apply_theme(qapp, "dark")
        apply_theme(qapp, "light")
        palette = qapp.palette()
        assert palette.color(QPalette.ColorRole.Window).lightness() > 128
