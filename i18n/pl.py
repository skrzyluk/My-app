STRINGS: dict[str, str] = {
    # Window / app
    "app_title":              "YouTube Notifier",
    "window_title":           "YouTube Notifier",

    # Tabs
    "tab_today":              "Dzisiaj",
    "tab_week":               "Tydzień",
    "tab_month":              "Miesiąc",

    # Buttons - main window
    "btn_refresh":            "↻ Odśwież",
    "btn_copy_all":           "Skopiuj wszystko",
    "btn_history":            "Historia",
    "btn_settings":           "Ustawienia",
    "btn_copy":               "Kopiuj",
    "btn_open_youtube":       "▶ Otwórz w YouTube",

    # Status labels
    "status_loading":         "Ładowanie…",
    "status_no_videos":       "Brak nowych filmów w tym okresie.",
    "status_error":           "Błąd ładowania.",
    "placeholder_no_videos":  "Brak filmów do wyświetlenia.",

    # Video count noun forms
    "video_singular":         "film",
    "video_2_4":              "filmy",
    "video_many":             "filmów",

    # Tray menu
    "tray_open":              "Otwórz",
    "tray_refresh":           "↻ Odśwież",
    "tray_quit":              "Wyjśdź",

    # Dialog titles (generic)
    "dlg_error":              "Błąd",

    # History dialog
    "dlg_history_title":      "Historia podsumowań",
    "lbl_no_summaries":       "Brak zapisanych podsumowań.",
    "btn_close":              "Zamknij",
    "lbl_videos_count_fmt":   "({} filmów)",

    # Settings dialog
    "dlg_settings_title":     "Ustawienia",
    "lbl_language":           "Język:",
    "lbl_theme":              "Motyw:",
    "lbl_notifications":      "Powiadomienia w tle:",
    "lang_polish":            "Polski",
    "lang_english":           "English",
    "theme_system":           "Systemowy",
    "theme_light":            "Jasny",
    "theme_dark":             "Ciemny",
    "btn_logout":             "Wyloguj się",
    "btn_cancel":             "Anuluj",
    "btn_save":               "Zapisz",
    "dlg_logout_title":       "Wylogowanie",
    "dlg_logout_msg":         "Czy na pewno chcesz się wylogować?",

    # Login window
    "btn_login":              "Zaloguj się przez Google",
    "status_logging_in":      "Logowanie…",
    "status_opening_browser": "Otwieranie przeglądarki…",
    "dlg_auth_error":         "Błąd logowania",

    # AI Chat panel
    "btn_chat_ai":            "\U0001f916 Czat AI",
    "chat_title":             "Asystent AI",
    "chat_close":             "Zamknij czat",
    "chat_placeholder":       "Zapytaj o filmy… (Enter = wyślij)",
    "chat_send":              "Wyślij",
    "chat_welcome":           "Cześć! Mam dostęp do {count} filmów z {period}. Mogę je podsumować, polecić co oglądać lub odpowiedzieć na pytania o tematykę. Co Cię interesuje?",
    "chat_no_api_key":        "Brak klucza Gemini API.\n\nPrzejdź do Ustawień i wpisz klucz w sekcji 'Klucz AI'. Klucz możesz uzyskać bezpłatnie na: aistudio.google.com",

    # Settings - AI key section
    "lbl_ai_key":             "Klucz Gemini API (bezpłatny):",
    "placeholder_ai_key":     "Wklej klucz API…",
    "tooltip_show_key":       "Pokaż / ukryj klucz",
    "hint_ai_key":            "Klucz zapisywany w Windows Credential Manager, nie w plikach. Darmowy klucz: aistudio.google.com",

    # Search
    "search_placeholder":     "Szukaj filmów…",

    # Video card
    "card_label_desc":        "OPIS",
    "btn_show_more":          "Pokaż więcej ▾",
    "btn_show_less":          "Pokaż mniej ▴",
    "btn_card_copy":          "📋 Kopiuj",
    "btn_card_youtube":       "▶ YouTube",
    "badge_new":              "NOWY",
    "card_no_channel":        "Kanał",

    # Status bar
    "status_ready":           "Gotowy",
    "statusbar_updated_fmt":  "Ostatnia aktualizacja: {time}",
    "statusbar_cache":        "Dane z cache",
    "statusbar_hint":         "↑↓ nawigacja · Enter otwórz · C kopiuj",
    "video_count_fmt":        "📺 {count} {noun}",

    # Settings – appearance
    "lbl_appearance":         "Motyw",
    "lbl_font_size":          "Rozmiar tekstu",
    "font_small":             "Mały",
    "font_normal":            "Normalny",
    "font_large":             "Duży",
    "font_xlarge":            "B. duży",
    "lbl_text_accessibility": "Dostępność tekstu",
    "lbl_white_text":         "Białe czcionki",
    "desc_white_text":        "Wszystkie etykiety i opisy w kolorze białym — niezależnie od motywu. Zwiększa czytelność na ciemnym tle.",
    "lbl_notif_title":        "Sprawdzaj w tle",
    "desc_notif":             "Powiadamiaj o nowych filmach co 24h.",
    "btn_save_close":         "Zapisz i zamknij",

    # Theme names
    "theme_dark_crimson":     "Dark Crimson",
    "theme_dark_ocean":       "Dark Ocean",
    "theme_dark_forest":      "Dark Forest",
    "theme_dark_violet":      "Dark Violet",
    "theme_dark_amber":       "Dark Amber",
    "theme_light_classic":    "Light Classic",
    "theme_high_contrast":    "High Contrast",
    "theme_system_label":     "Systemowy",

    # AI panel
    "chat_subtitle":          "Gemini · tylko twoje filmy",
    "chat_subtitle_ollama":   "Ollama · tylko twoje filmy",
    "chat_ready":             "gotowy",
    "chat_note":              "Dane nie opuszczają urządzenia",

    # AI provider settings
    "lbl_ai_section":         "Asystent AI",
    "ai_provider_gemini":     "Google Gemini (chmura)",
    "ai_provider_ollama":     "Ollama (lokalnie, bezpłatnie)",
    "lbl_ollama_url":         "Adres Ollama:",
    "lbl_ollama_model":       "Model:",
    "hint_ollama":            "Ollama musi być uruchomione lokalnie. Pobierz model: ollama pull llama3.2",
    "btn_test_ollama":        "🔌 Testuj połączenie",
    "chat_no_ollama":         "Nie można połączyć się z Ollama.\n\nUpewnij się, że Ollama jest zainstalowane i uruchomione.\nSzczegóły: {error}",
}
