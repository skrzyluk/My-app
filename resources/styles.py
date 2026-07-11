"""QSS stylesheets for YouTube Notifier – token-based theme engine (Phase 9).

Design reference: ``mockup-final-v4.html`` + ``DESIGN_DECISIONS.md``.

Instead of two hand-written stylesheets, the styling is now a single QSS
*template* (``_TEMPLATE``) whose colours and font sizes are ``${token}``
placeholders.  Each named theme in :data:`THEMES` supplies a set of token
values – mirroring the CSS custom properties from the mockup.  Themes are
applied at runtime with :func:`build_qss`, so switching theme / font size /
white-text mode never requires an app restart.

Public API
----------
* :data:`THEMES`           – ordered mapping ``theme_id -> token dict``
* :data:`FONT_SCALES`      – ``size_id -> float`` multipliers
* :func:`build_qss`        – render the template for a theme
* :data:`DARK_QSS`         – ``build_qss("dark-crimson")``  (back-compat)
* :data:`LIGHT_QSS`        – ``build_qss("light-classic")`` (back-compat)
"""

from __future__ import annotations

import string

# ─────────────────────────────────────────────────────────────────────────── #
#  Theme tokens (mirror the CSS custom properties in mockup-final-v4.html)    #
# ─────────────────────────────────────────────────────────────────────────── #

DEFAULT_THEME = "dark-crimson"

#: All selectable colour themes, in display order.
THEMES: dict[str, dict[str, str]] = {
    "dark-crimson": {
        "bg_app": "#0f0f0f", "bg_surface": "#141414", "bg_card": "#1c1c1c",
        "bg_hover": "#242424", "bg_input": "#1c1c1c", "bg_titlebar": "#0a0a0a",
        "bg_statusbar": "#141414",
        "accent": "#ff0000", "accent_hover": "#cc0000",
        "accent_subtle": "rgba(255, 0, 0, 0.10)", "accent_border": "rgba(255, 0, 0, 0.30)",
        "text_primary": "#e8e8e8", "text_secondary": "#aaaaaa",
        "text_muted": "#555555", "text_on_accent": "#ffffff",
        "border": "#2a2a2a", "border_strong": "#444444",
    },
    "dark-ocean": {
        "bg_app": "#060d1a", "bg_surface": "#0d1a2e", "bg_card": "#101e30",
        "bg_hover": "#14263a", "bg_input": "#0d1a2e", "bg_titlebar": "#040a14",
        "bg_statusbar": "#0d1a2e",
        "accent": "#0ea5e9", "accent_hover": "#0284c7",
        "accent_subtle": "rgba(14, 165, 233, 0.10)", "accent_border": "rgba(14, 165, 233, 0.30)",
        "text_primary": "#e0e8f0", "text_secondary": "#7fa3c4",
        "text_muted": "#3a5a7a", "text_on_accent": "#ffffff",
        "border": "#0d2040", "border_strong": "#1a3a5a",
    },
    "dark-forest": {
        "bg_app": "#071210", "bg_surface": "#0d1f1a", "bg_card": "#101e18",
        "bg_hover": "#162818", "bg_input": "#0d1f1a", "bg_titlebar": "#040e0c",
        "bg_statusbar": "#0d1f1a",
        "accent": "#22c55e", "accent_hover": "#16a34a",
        "accent_subtle": "rgba(34, 197, 94, 0.10)", "accent_border": "rgba(34, 197, 94, 0.30)",
        "text_primary": "#e0f0e8", "text_secondary": "#5a9a6e",
        "text_muted": "#2a5a3a", "text_on_accent": "#ffffff",
        "border": "#0d2e1a", "border_strong": "#1a4a28",
    },
    "dark-violet": {
        "bg_app": "#0d0a1a", "bg_surface": "#14102a", "bg_card": "#181428",
        "bg_hover": "#201a32", "bg_input": "#14102a", "bg_titlebar": "#080612",
        "bg_statusbar": "#14102a",
        "accent": "#a855f7", "accent_hover": "#9333ea",
        "accent_subtle": "rgba(168, 85, 247, 0.10)", "accent_border": "rgba(168, 85, 247, 0.30)",
        "text_primary": "#ece0ff", "text_secondary": "#9a7ac4",
        "text_muted": "#4a2a7a", "text_on_accent": "#ffffff",
        "border": "#1e1040", "border_strong": "#301860",
    },
    "dark-amber": {
        "bg_app": "#0f0c06", "bg_surface": "#1c160c", "bg_card": "#201a10",
        "bg_hover": "#2a2214", "bg_input": "#1c160c", "bg_titlebar": "#0a0804",
        "bg_statusbar": "#1c160c",
        "accent": "#f59e0b", "accent_hover": "#d97706",
        "accent_subtle": "rgba(245, 158, 11, 0.10)", "accent_border": "rgba(245, 158, 11, 0.30)",
        "text_primary": "#f0e8d0", "text_secondary": "#b8923a",
        "text_muted": "#5a4210", "text_on_accent": "#000000",
        "border": "#2a1e06", "border_strong": "#4a3a12",
    },
    "light-classic": {
        "bg_app": "#f5f5f5", "bg_surface": "#ebebeb", "bg_card": "#ffffff",
        "bg_hover": "#f0f0f0", "bg_input": "#ffffff", "bg_titlebar": "#e0e0e0",
        "bg_statusbar": "#ebebeb",
        "accent": "#cc0000", "accent_hover": "#aa0000",
        "accent_subtle": "rgba(204, 0, 0, 0.08)", "accent_border": "rgba(204, 0, 0, 0.25)",
        "text_primary": "#111111", "text_secondary": "#555555",
        "text_muted": "#999999", "text_on_accent": "#ffffff",
        "border": "#dddddd", "border_strong": "#bbbbbb",
    },
    "high-contrast": {
        "bg_app": "#000000", "bg_surface": "#000000", "bg_card": "#000000",
        "bg_hover": "#1a1a1a", "bg_input": "#000000", "bg_titlebar": "#000000",
        "bg_statusbar": "#000000",
        "accent": "#ffff00", "accent_hover": "#e6e600",
        "accent_subtle": "rgba(255, 255, 0, 0.10)", "accent_border": "#ffff00",
        "text_primary": "#ffffff", "text_secondary": "#ffffff",
        "text_muted": "#cccccc", "text_on_accent": "#000000",
        "border": "#ffffff", "border_strong": "#ffffff",
    },
}

#: ``theme_id -> True`` when the theme is a light variant (drives the palette).
LIGHT_THEMES = {"light-classic"}

#: Legacy theme names (stored in older settings) → new theme ids.
_THEME_ALIASES = {"dark": "dark-crimson", "light": "light-classic"}

#: Font-size presets (DESIGN_DECISIONS §10: Mały / Normalny / Duży / B. duży).
FONT_SCALES: dict[str, float] = {
    "small": 0.92,
    "normal": 1.0,
    "large": 1.15,
    "xlarge": 1.30,
}

#: Base font sizes (px) keyed by template token; scaled by the active preset.
_FONT_BASES: dict[str, int] = {
    "fs_xs": 10,
    "fs_sm": 11,
    "fs_base": 12,
    "fs_md": 13,
    "fs_lg": 15,
    "fs_xl": 22,
}


# ─────────────────────────────────────────────────────────────────────────── #
#  QSS template                                                               #
# ─────────────────────────────────────────────────────────────────────────── #

_TEMPLATE = string.Template("""
/* ──── Base ──────────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: ${fs_md}px;
    color: ${text_primary};
}

QMainWindow, #central_widget {
    background-color: ${bg_app};
}

QDialog {
    background-color: ${bg_surface};
}

QWidget {
    background-color: transparent;
}

QToolTip {
    background-color: ${bg_surface};
    color: ${text_primary};
    border: 1px solid ${border};
    padding: 4px 8px;
}

/* ──── Toolbar (period tabs + count + actions) ───────────────────────────── */
#toolbar {
    background-color: ${bg_app};
    border-bottom: 1px solid ${border};
}

#tab_group {
    background-color: ${bg_surface};
    border: 1px solid ${border};
    border-radius: 8px;
}

QPushButton[tab="true"] {
    background-color: transparent;
    color: ${text_secondary};
    border: none;
    border-radius: 5px;
    padding: 5px 16px;
    font-size: ${fs_base}px;
    font-weight: 500;
    min-width: 64px;
}

QPushButton[tab="true"]:checked {
    background-color: ${accent};
    color: ${text_on_accent};
    font-weight: 700;
}

QPushButton[tab="true"]:hover:!checked {
    background-color: ${bg_hover};
    color: ${text_primary};
}

#video_count {
    color: ${text_secondary};
    font-size: ${fs_sm}px;
    background-color: ${bg_surface};
    border: 1px solid ${border};
    border-radius: 5px;
    padding: 4px 10px;
}

/* ──── Toolbar buttons (ghost) ───────────────────────────────────────────── */
QPushButton[tbtn="true"] {
    background-color: ${bg_surface};
    color: ${text_secondary};
    border: 1px solid ${border};
    border-radius: 6px;
    padding: 6px 11px;
    font-size: ${fs_sm}px;
    font-weight: 500;
}

QPushButton[tbtn="true"]:hover {
    background-color: ${bg_hover};
    border-color: ${border_strong};
    color: ${text_primary};
}

QPushButton[tbtn="true"]:disabled {
    color: ${text_muted};
    border-color: ${border};
}

/* Refresh – primary accent fill */
#refresh_btn {
    background-color: ${accent};
    color: ${text_on_accent};
    border: 1px solid ${accent};
    border-radius: 6px;
    font-weight: 700;
    padding: 6px 13px;
    font-size: ${fs_sm}px;
}
#refresh_btn:hover { background-color: ${accent_hover}; border-color: ${accent_hover}; }
#refresh_btn:disabled { background-color: ${bg_surface}; color: ${text_muted}; border-color: ${border}; }

/* AI Chat toggle */
#ai_toggle_btn {
    background-color: rgba(99, 102, 241, 0.10);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.30);
    border-radius: 6px;
    padding: 6px 11px;
    font-size: ${fs_sm}px;
    font-weight: 500;
}
#ai_toggle_btn:hover { background-color: rgba(99, 102, 241, 0.20); }
#ai_toggle_btn:checked { background-color: rgba(99, 102, 241, 0.28); border-color: #6366f1; color: #c7d2fe; }

/* ──── Search bar ────────────────────────────────────────────────────────── */
#search_wrap {
    background-color: ${bg_app};
    border-bottom: 1px solid ${border};
}

#search_input {
    background-color: ${bg_input};
    border: 1px solid ${border};
    border-radius: 6px;
    color: ${text_primary};
    font-size: ${fs_base}px;
    padding: 7px 12px;
}
#search_input:focus { border-color: ${accent}; }

/* ──── Generic buttons ───────────────────────────────────────────────────── */
QPushButton {
    background-color: ${bg_surface};
    color: ${text_secondary};
    border: 1px solid ${border};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}
QPushButton:hover { background-color: ${bg_hover}; border-color: ${border_strong}; color: ${text_primary}; }
QPushButton:pressed { background-color: ${bg_hover}; }
QPushButton:disabled { color: ${text_muted}; background-color: ${bg_surface}; border-color: ${border}; }

/* ──── Tiles scroll area ─────────────────────────────────────────────────── */
#tiles_scroll, #tiles_container {
    background-color: ${bg_app};
    border: none;
}

QScrollArea { background-color: ${bg_app}; border: none; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: ${border}; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: ${border_strong}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { height: 0px; }

/* ──── Video card ────────────────────────────────────────────────────────── */
#video_card {
    background-color: ${bg_card};
    border: 1px solid ${border};
    border-radius: 10px;
}
#video_card:hover { border-color: ${border_strong}; }
#video_card[selected="true"] { border-color: ${accent}; }

#card_thumb { background-color: ${bg_surface}; border-radius: 8px; }

#thumb_placeholder { color: ${accent}; background-color: transparent; }

#card_dur {
    background-color: rgba(0, 0, 0, 0.85);
    color: #ffffff;
    font-size: ${fs_xs}px;
    font-weight: 700;
    border-radius: 3px;
    padding: 1px 5px;
}

#card_new {
    background-color: ${accent};
    color: ${text_on_accent};
    font-size: ${fs_xs}px;
    font-weight: 800;
    border-radius: 3px;
    padding: 1px 6px;
}

#card_avatar {
    color: #ffffff;
    font-size: ${fs_sm}px;
    font-weight: 700;
    border-radius: 13px;
}

#card_channel_name { color: ${text_secondary}; font-size: ${fs_base}px; font-weight: 500; background: transparent; }
#card_date { color: ${text_muted}; font-size: ${fs_xs}px; background: transparent; }
#card_title { color: ${text_primary}; font-size: ${fs_md}px; font-weight: 700; background: transparent; }
#card_sep { background-color: ${border}; max-height: 1px; min-height: 1px; border: none; }
#card_desc_label { color: ${text_muted}; font-size: ${fs_xs}px; font-weight: 700; background: transparent; }
#card_desc { color: ${text_secondary}; font-size: ${fs_base}px; background: transparent; }

#toggle_desc_btn {
    color: ${accent};
    background: transparent;
    border: none;
    font-size: ${fs_sm}px;
    font-weight: 600;
    text-align: left;
    padding: 0px;
}
#toggle_desc_btn:hover { color: ${accent_hover}; }

QPushButton[card_btn="true"] {
    background-color: ${bg_surface};
    color: ${text_secondary};
    border: 1px solid ${border};
    border-radius: 6px;
    font-size: ${fs_sm}px;
    font-weight: 600;
    padding: 7px 6px;
}
QPushButton[card_btn="true"]:hover { background-color: ${bg_hover}; border-color: ${border_strong}; color: ${text_primary}; }

QPushButton[card_btn="yt"] {
    background-color: ${accent_subtle};
    color: ${accent};
    border: 1px solid ${accent_border};
    border-radius: 6px;
    font-size: ${fs_sm}px;
    font-weight: 600;
    padding: 7px 6px;
}
QPushButton[card_btn="yt"]:hover { background-color: ${accent}; color: ${text_on_accent}; border-color: ${accent}; }

/* ──── Status bar ────────────────────────────────────────────────────────── */
#statusbar {
    background-color: ${bg_statusbar};
    border-top: 1px solid ${border};
}
#status_text { color: ${text_secondary}; font-size: ${fs_sm}px; background: transparent; }
#status_hint { color: ${text_muted}; font-size: ${fs_sm}px; background: transparent; }

/* ──── Empty state ───────────────────────────────────────────────────────── */
#empty_icon { color: ${border_strong}; background: transparent; }
#empty_text { color: ${text_secondary}; font-size: ${fs_lg}px; font-weight: 600; background: transparent; }
#empty_hint { color: ${text_muted}; font-size: ${fs_base}px; background: transparent; }
#status_label { color: ${text_muted}; font-size: ${fs_sm}px; background: transparent; }

/* ──── Inputs ────────────────────────────────────────────────────────────── */
QComboBox {
    background-color: ${bg_input};
    border: 1px solid ${border};
    border-radius: 6px;
    padding: 6px 10px;
    color: ${text_primary};
}
QComboBox:hover { border-color: ${border_strong}; }
QComboBox:focus { border-color: ${accent}; }
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background: ${bg_surface};
    border: 1px solid ${border};
    border-radius: 6px;
    color: ${text_primary};
    selection-background-color: ${accent_subtle};
    selection-color: ${accent};
    outline: none;
    padding: 2px;
}

QCheckBox { spacing: 8px; color: ${text_secondary}; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 2px solid ${border_strong};
    border-radius: 4px;
    background-color: ${bg_input};
}
QCheckBox::indicator:checked { background-color: ${accent}; border-color: ${accent}; }
QCheckBox::indicator:hover { border-color: ${accent}; }

QLineEdit {
    background-color: ${bg_input};
    border: 1px solid ${border};
    border-radius: 6px;
    padding: 6px 10px;
    color: ${text_primary};
}
QLineEdit:focus { border-color: ${accent}; }
QLineEdit:hover { border-color: ${border_strong}; }

/* ──── Separators ────────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: ${border};
    background-color: ${border};
    max-height: 1px;
}

/* ──── QMenu (tray + context) ────────────────────────────────────────────── */
QMenu {
    background-color: ${bg_surface};
    border: 1px solid ${border};
    border-radius: 8px;
    padding: 4px;
}
QMenu::item { padding: 6px 16px; border-radius: 5px; color: ${text_secondary}; }
QMenu::item:selected { background-color: ${bg_hover}; color: ${text_primary}; }
QMenu::separator { height: 1px; background-color: ${border}; margin: 4px 8px; }

/* ──── Settings dialog ───────────────────────────────────────────────────── */
#settings_section_label {
    color: ${text_muted};
    font-size: ${fs_xs}px;
    font-weight: 700;
    background: transparent;
}
#settings_hint { color: ${text_muted}; font-size: ${fs_sm}px; background: transparent; }

QPushButton[swatch="true"] {
    border: 2px solid ${border};
    border-radius: 8px;
    padding: 6px 10px;
    background-color: ${bg_surface};
    color: ${text_secondary};
    font-size: ${fs_sm}px;
    font-weight: 600;
    text-align: left;
}
QPushButton[swatch="true"]:hover { border-color: ${border_strong}; color: ${text_primary}; }
QPushButton[swatch="true"]:checked { border-color: ${accent}; background-color: ${accent_subtle}; color: ${text_primary}; }

QPushButton[fontbtn="true"] {
    border: 1px solid ${border};
    border-radius: 6px;
    background-color: ${bg_surface};
    color: ${text_secondary};
    padding: 6px 4px;
    font-weight: 600;
}
QPushButton[fontbtn="true"]:hover { background-color: ${bg_hover}; }
QPushButton[fontbtn="true"]:checked { border-color: ${accent}; background-color: ${accent_subtle}; color: ${text_primary}; }

#btn_logout {
    background-color: rgba(239, 68, 68, 0.08);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.30);
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}
#btn_logout:hover { background-color: rgba(239, 68, 68, 0.18); color: #ffffff; border-color: #f87171; }

#btn_save {
    background-color: ${accent};
    color: ${text_on_accent};
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 700;
}
#btn_save:hover { background-color: ${accent_hover}; }

#api_key_input { font-size: ${fs_base}px; }

/* ──── Login window ──────────────────────────────────────────────────────── */
#login_title { color: ${text_primary}; font-size: ${fs_xl}px; font-weight: 700; background: transparent; }
#login_logo { color: ${accent}; background: transparent; }
#login_status { color: ${text_muted}; font-size: ${fs_base}px; background: transparent; }
#login_btn {
    background-color: ${accent};
    color: ${text_on_accent};
    border: none;
    border-radius: 8px;
    padding: 10px 32px;
    font-size: ${fs_md}px;
    font-weight: 600;
}
#login_btn:hover { background-color: ${accent_hover}; }
#login_btn:disabled { background-color: ${bg_surface}; color: ${text_muted}; }

/* ──── History dialog ────────────────────────────────────────────────────── */
#history_card {
    background-color: ${bg_card};
    border: 1px solid ${border};
    border-radius: 10px;
}
#history_date { color: ${text_primary}; font-weight: 700; font-size: ${fs_md}px; background: transparent; }
#history_period { color: ${text_secondary}; font-size: ${fs_base}px; background: transparent; }
#history_count { color: ${text_muted}; font-size: ${fs_sm}px; background: transparent; }
#history_preview { color: ${text_secondary}; font-size: ${fs_base}px; background: transparent; }
#history_empty { color: ${text_muted}; font-size: ${fs_md}px; background: transparent; }

/* ──── AI chat side panel ────────────────────────────────────────────────── */
#ai_chat_panel { background-color: ${bg_surface}; border-left: 1px solid ${border}; }
#chat_header { background-color: ${bg_titlebar}; border-bottom: 1px solid ${border}; }
#chat_header_title { color: ${text_primary}; font-size: ${fs_md}px; font-weight: 700; background: transparent; }
#chat_subtitle { color: ${text_muted}; font-size: ${fs_xs}px; background: transparent; }
#chat_live { color: #34d399; font-size: ${fs_xs}px; background: transparent; }
#chat_close_btn {
    background-color: transparent;
    color: ${text_secondary};
    border: none;
    border-radius: 5px;
    font-size: ${fs_md}px;
}
#chat_close_btn:hover { background-color: ${bg_hover}; color: ${text_primary}; }
#chat_new_btn {
    background-color: transparent;
    color: ${text_secondary};
    border: none;
    border-radius: 5px;
    font-size: ${fs_sm}px;
}
#chat_new_btn:hover { background-color: ${bg_hover}; color: ${text_primary}; }
#chat_copy_btn {
    background-color: transparent;
    color: ${text_muted};
    border: none;
    border-radius: 4px;
    font-size: ${fs_sm}px;
}
#chat_copy_btn:hover { background-color: ${bg_hover}; color: ${text_primary}; }

#quick_bar { background-color: ${bg_surface}; border-bottom: 1px solid ${border}; }
#quick_prompt_btn {
    background-color: ${bg_card};
    color: ${text_secondary};
    border: 1px solid ${border};
    border-radius: 12px;
    padding: 4px 10px;
    font-size: ${fs_sm}px;
    text-align: left;
}
#quick_prompt_btn:hover { border-color: #6366f1; color: #a5b4fc; background-color: rgba(99, 102, 241, 0.10); }

#msg_container { background-color: ${bg_app}; }

#bubble_user {
    background-color: ${accent};
    border: 1px solid ${accent};
    border-radius: 10px;
}
#bubble_user QLabel { color: ${text_on_accent}; background: transparent; }

#bubble_assistant {
    background-color: ${bg_card};
    border: 1px solid ${border};
    border-radius: 10px;
}
#bubble_assistant QLabel { color: ${text_primary}; background: transparent; }

#bubble_system {
    background-color: transparent;
    border: 1px solid ${border};
    border-radius: 8px;
}
#bubble_system QLabel { color: ${text_secondary}; background: transparent; }

#chat_input_bar { background-color: ${bg_surface}; border-top: 1px solid ${border}; }
#chat_input {
    background-color: ${bg_card};
    border: 1px solid ${border};
    border-radius: 8px;
    padding: 7px 10px;
    color: ${text_primary};
    font-size: ${fs_sm}px;
}
#chat_input:focus { border-color: #6366f1; }
#chat_send_btn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 7px;
    font-weight: 700;
    font-size: ${fs_md}px;
}
#chat_send_btn:hover { background-color: #7c7ff5; }
#chat_send_btn:disabled { background-color: ${bg_hover}; color: ${text_muted}; }
#chat_note { color: ${text_muted}; font-size: ${fs_xs}px; background: transparent; }
""")


# ─────────────────────────────────────────────────────────────────────────── #
#  Rendering                                                                  #
# ─────────────────────────────────────────────────────────────────────────── #

def resolve_theme(theme: str | None) -> str:
    """Map a stored/legacy theme name to a known theme id."""
    if not theme:
        return DEFAULT_THEME
    if theme in THEMES:
        return theme
    return _THEME_ALIASES.get(theme, DEFAULT_THEME)


def build_qss(
    theme: str = DEFAULT_THEME,
    *,
    white_text: bool = False,
    font_scale: str = "normal",
) -> str:
    """Render the QSS template for *theme*.

    :param theme:      a key of :data:`THEMES` (or a legacy ``dark``/``light``).
    :param white_text: force all text tokens to white (accessibility toggle).
    :param font_scale: a key of :data:`FONT_SCALES`.
    """
    tokens = dict(THEMES[resolve_theme(theme)])

    if white_text:
        tokens["text_primary"] = "#ffffff"
        tokens["text_secondary"] = "#ffffff"
        tokens["text_muted"] = "#cccccc"

    scale = FONT_SCALES.get(font_scale, 1.0)
    for token, base in _FONT_BASES.items():
        tokens[token] = str(max(1, round(base * scale)))

    return _TEMPLATE.substitute(tokens)


# ─────────────────────────────────────────────────────────────────────────── #
#  Back-compat module constants                                               #
# ─────────────────────────────────────────────────────────────────────────── #

DARK_QSS = build_qss("dark-crimson")
LIGHT_QSS = build_qss("light-classic")
