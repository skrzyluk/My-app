"""QSS stylesheets for YouTube Notifier – Light and Dark themes."""

# ─────────────────────────────────────────────────────────────────────────── #
#  LIGHT                                                                      #
# ─────────────────────────────────────────────────────────────────────────── #

LIGHT_QSS = """
/* ──── Base ──────────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #F5F5F5;
}

QDialog {
    background-color: #FFFFFF;
}

QWidget {
    background-color: transparent;
}

/* ──── Header bar ─────────────────────────────────────────────────────────── */
#header_bar {
    background-color: #FFFFFF;
    border-bottom: 2px solid #E53935;
}

#header_logo {
    font-size: 22px;
    background-color: transparent;
}

#header_title {
    font-size: 17px;
    font-weight: 700;
    color: #E53935;
    background-color: transparent;
    letter-spacing: 0px;
}

/* ──── Tab bar ────────────────────────────────────────────────────────────── */
#tab_bar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EEEEEE;
}

QPushButton[tab="true"] {
    background-color: transparent;
    color: #757575;
    border: none;
    border-radius: 14px;
    padding: 4px 20px;
    font-weight: 600;
    min-width: 80px;
}

QPushButton[tab="true"]:checked {
    background-color: #E53935;
    color: #FFFFFF;
}

QPushButton[tab="true"]:hover:!checked {
    background-color: #EEEEEE;
    color: #212121;
}

/* ──── Buttons (general) ─────────────────────────────────────────────────── */
QPushButton {
    background-color: #EEEEEE;
    color: #212121;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #E0E0E0;
    border-color: #BDBDBD;
}

QPushButton:pressed {
    background-color: #BDBDBD;
}

QPushButton:disabled {
    color: #BDBDBD;
    background-color: #F5F5F5;
    border-color: #EEEEEE;
}

/* Refresh – primary (red fill) */
#refresh_btn {
    background-color: #E53935;
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}

#refresh_btn:hover {
    background-color: #C62828;
}

#refresh_btn:pressed {
    background-color: #B71C1C;
}

#refresh_btn:disabled {
    background-color: #FFCDD2;
    color: #EF9A9A;
}

/* Copy All – outlined */
#copy_all_btn {
    background-color: transparent;
    color: #E53935;
    border: 1.5px solid #E53935;
    font-weight: 600;
}

#copy_all_btn:hover {
    background-color: #FFEBEE;
}

#copy_all_btn:disabled {
    color: #BDBDBD;
    border-color: #BDBDBD;
}

/* Copy button on each video card */
#card_copy_btn {
    background-color: transparent;
    color: #9E9E9E;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
}

#card_copy_btn:hover {
    background-color: #FFEBEE;
    color: #E53935;
    border-color: #E53935;
}

/* ──── Action bar ─────────────────────────────────────────────────────────── */
#action_bar {
    background-color: #FFFFFF;
    border-top: 1px solid #EEEEEE;
}

/* ──── Video cards ────────────────────────────────────────────────────────── */
#video_card {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
}

#video_card:hover {
    border: 1.5px solid #E53935;
}

/* ──── Scroll area / bar ──────────────────────────────────────────────────── */
QScrollArea {
    background-color: #F5F5F5;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #AAAAAA;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ──── ComboBox ───────────────────────────────────────────────────────────── */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 5px 10px;
    color: #212121;
}

QComboBox:hover { border-color: #E53935; }
QComboBox:focus { border-color: #E53935; outline: none; }

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    selection-background-color: #FFEBEE;
    selection-color: #E53935;
    outline: none;
    padding: 2px;
}

/* ──── CheckBox ───────────────────────────────────────────────────────────── */
QCheckBox { spacing: 8px; }

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #CCCCCC;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #E53935;
    border-color: #E53935;
}

QCheckBox::indicator:hover { border-color: #E53935; }

/* ──── Labels ─────────────────────────────────────────────────────────────── */
#status_label {
    color: #9E9E9E;
    font-size: 12px;
    background-color: transparent;
}

#empty_icon {
    color: #DDDDDD;
    background-color: transparent;
}

#empty_text {
    color: #BDBDBD;
    font-size: 15px;
    font-weight: 600;
    background-color: transparent;
}

#empty_hint {
    color: #CCCCCC;
    font-size: 12px;
    background-color: transparent;
}

#video_title {
    color: #212121;
    font-size: 14px;
    background-color: transparent;
}

#video_meta {
    color: #9E9E9E;
    font-size: 12px;
    background-color: transparent;
}

#video_desc {
    color: #757575;
    font-size: 12px;
    background-color: transparent;
}

/* ──── Separators ─────────────────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #EEEEEE;
    background-color: #EEEEEE;
}
"""

# ─────────────────────────────────────────────────────────────────────────── #
#  DARK                                                                       #
# ─────────────────────────────────────────────────────────────────────────── #

DARK_QSS = """
/* ──── Base ──────────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #E8EAED;
}

QMainWindow {
    background-color: #121212;
}

QDialog {
    background-color: #1E1E1E;
}

QWidget {
    background-color: transparent;
}

/* ──── Header bar ─────────────────────────────────────────────────────────── */
#header_bar {
    background-color: #1E1E1E;
    border-bottom: 2px solid #EF5350;
}

#header_logo {
    font-size: 22px;
    background-color: transparent;
}

#header_title {
    font-size: 17px;
    font-weight: 700;
    color: #EF5350;
    background-color: transparent;
}

/* ──── Tab bar ────────────────────────────────────────────────────────────── */
#tab_bar {
    background-color: #1E1E1E;
    border-bottom: 1px solid #2D2D2D;
}

QPushButton[tab="true"] {
    background-color: transparent;
    color: #9E9E9E;
    border: none;
    border-radius: 14px;
    padding: 4px 20px;
    font-weight: 600;
    min-width: 80px;
}

QPushButton[tab="true"]:checked {
    background-color: #EF5350;
    color: #FFFFFF;
}

QPushButton[tab="true"]:hover:!checked {
    background-color: #2D2D2D;
    color: #E8EAED;
}

/* ──── Buttons (general) ─────────────────────────────────────────────────── */
QPushButton {
    background-color: #2D2D2D;
    color: #E8EAED;
    border: 1px solid #3C3C3C;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3C3C3C;
    border-color: #505050;
}

QPushButton:pressed {
    background-color: #4D4D4D;
}

QPushButton:disabled {
    color: #555555;
    background-color: #1E1E1E;
    border-color: #2D2D2D;
}

#refresh_btn {
    background-color: #EF5350;
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}

#refresh_btn:hover { background-color: #E53935; }
#refresh_btn:pressed { background-color: #C62828; }

#refresh_btn:disabled {
    background-color: #4A2020;
    color: #7D4040;
}

#copy_all_btn {
    background-color: transparent;
    color: #EF5350;
    border: 1.5px solid #EF5350;
    font-weight: 600;
}

#copy_all_btn:hover { background-color: #3D1F1F; }

#copy_all_btn:disabled {
    color: #555555;
    border-color: #555555;
}

#card_copy_btn {
    background-color: transparent;
    color: #757575;
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
}

#card_copy_btn:hover {
    background-color: #3D1F1F;
    color: #EF5350;
    border-color: #EF5350;
}

/* ──── Action bar ─────────────────────────────────────────────────────────── */
#action_bar {
    background-color: #1E1E1E;
    border-top: 1px solid #2D2D2D;
}

/* ──── Video cards ────────────────────────────────────────────────────────── */
#video_card {
    background-color: #1E1E1E;
    border: 1px solid #2D2D2D;
    border-radius: 8px;
}

#video_card:hover {
    border: 1.5px solid #EF5350;
}

/* ──── Scroll area / bar ──────────────────────────────────────────────────── */
QScrollArea {
    background-color: #121212;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #444444;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover { background: #666666; }

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ──── ComboBox ───────────────────────────────────────────────────────────── */
QComboBox {
    background-color: #2D2D2D;
    border: 1px solid #3C3C3C;
    border-radius: 6px;
    padding: 5px 10px;
    color: #E8EAED;
}

QComboBox:hover { border-color: #EF5350; }
QComboBox:focus { border-color: #EF5350; outline: none; }

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background: #2D2D2D;
    border: 1px solid #3C3C3C;
    color: #E8EAED;
    selection-background-color: #3D1F1F;
    selection-color: #EF5350;
    outline: none;
    padding: 2px;
}

/* ──── CheckBox ───────────────────────────────────────────────────────────── */
QCheckBox { spacing: 8px; color: #E8EAED; }

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #555555;
    border-radius: 4px;
    background-color: #2D2D2D;
}

QCheckBox::indicator:checked {
    background-color: #EF5350;
    border-color: #EF5350;
}

QCheckBox::indicator:hover { border-color: #EF5350; }

/* ──── Labels ─────────────────────────────────────────────────────────────── */
#status_label {
    color: #757575;
    font-size: 12px;
    background-color: transparent;
}

#empty_icon {
    color: #444444;
    background-color: transparent;
}

#empty_text {
    color: #555555;
    font-size: 15px;
    font-weight: 600;
    background-color: transparent;
}

#empty_hint {
    color: #444444;
    font-size: 12px;
    background-color: transparent;
}

#video_title {
    color: #E8EAED;
    font-size: 14px;
    background-color: transparent;
}

#video_meta {
    color: #757575;
    font-size: 12px;
    background-color: transparent;
}

#video_desc {
    color: #9AA0A6;
    font-size: 12px;
    background-color: transparent;
}

/* ──── Separators ─────────────────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #2D2D2D;
    background-color: #2D2D2D;
}
"""
