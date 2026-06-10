STRINGS: dict[str, str] = {
    # Window / app
    "app_title":              "YouTube Notifier",
    "window_title":           "YouTube Notifier",

    # Tabs
    "tab_today":              "Today",
    "tab_week":               "Week",
    "tab_month":              "Month",

    # Buttons - main window
    "btn_refresh":            "↻ Refresh",
    "btn_copy_all":           "Copy All",
    "btn_history":            "History",
    "btn_settings":           "Settings",
    "btn_copy":               "Copy",
    "btn_open_youtube":       "▶ Open in YouTube",

    # Status labels
    "status_loading":         "Loading…",
    "status_no_videos":       "No new videos in this period.",
    "status_error":           "Loading error.",
    "placeholder_no_videos":  "No videos to display.",

    # Video count noun forms
    "video_singular":         "video",
    "video_2_4":              "videos",
    "video_many":             "videos",

    # Tray menu
    "tray_open":              "Open",
    "tray_refresh":           "↻ Refresh",
    "tray_quit":              "Quit",

    # Dialog titles (generic)
    "dlg_error":              "Error",

    # History dialog
    "dlg_history_title":      "Summary History",
    "lbl_no_summaries":       "No saved summaries.",
    "btn_close":              "Close",
    "lbl_videos_count_fmt":   "({} videos)",

    # Settings dialog
    "dlg_settings_title":     "Settings",
    "lbl_language":           "Language:",
    "lbl_theme":              "Theme:",
    "lbl_notifications":      "Background notifications:",
    "lang_polish":            "Polski",
    "lang_english":           "English",
    "theme_system":           "System",
    "theme_light":            "Light",
    "theme_dark":             "Dark",
    "btn_logout":             "Log out",
    "btn_cancel":             "Cancel",
    "btn_save":               "Save",
    "dlg_logout_title":       "Log Out",
    "dlg_logout_msg":         "Are you sure you want to log out?",

    # Login window
    "btn_login":              "Sign in with Google",
    "status_logging_in":      "Logging in…",
    "status_opening_browser": "Opening browser…",
    "dlg_auth_error":         "Authentication Error",

    # AI Chat panel
    "btn_chat_ai":            "\U0001f916 AI Chat",
    "chat_title":             "AI Assistant",
    "chat_close":             "Close chat",
    "chat_placeholder":       "Ask about videos… (Enter = send)",
    "chat_send":              "Send",
    "chat_welcome":           "Hi! I have access to {count} videos from {period}. I can summarize them, recommend what to watch, or answer questions about their topics. What would you like to know?",
    "chat_no_api_key":        "Gemini API key not set.\n\nGo to Settings and enter a key in the 'AI Key' section. Get a free key at: aistudio.google.com",

    # Settings - AI key section
    "lbl_ai_key":             "Gemini API Key (free):",
    "placeholder_ai_key":     "Paste your API key…",
    "tooltip_show_key":       "Show / hide key",
    "hint_ai_key":            "Key stored in Windows Credential Manager, not in files. Free key at: aistudio.google.com",

    # Search
    "search_placeholder":     "Search videos…",

    # Video card
    "card_label_desc":        "DESCRIPTION",
    "btn_show_more":          "Show more ▾",
    "btn_show_less":          "Show less ▴",
    "btn_card_copy":          "📋 Copy",
    "btn_card_youtube":       "▶ YouTube",
    "badge_new":              "NEW",
    "card_no_channel":        "Channel",

    # Status bar
    "status_ready":           "Ready",
    "statusbar_updated_fmt":  "Last update: {time}",
    "statusbar_cache":        "Cached data",
    "statusbar_hint":         "↑↓ navigate · Enter open · C copy",
    "video_count_fmt":        "📺 {count} {noun}",

    # Settings – appearance
    "lbl_appearance":         "Theme",
    "lbl_font_size":          "Text size",
    "font_small":             "Small",
    "font_normal":            "Normal",
    "font_large":             "Large",
    "font_xlarge":            "X-Large",
    "lbl_text_accessibility": "Text accessibility",
    "lbl_white_text":         "White text",
    "desc_white_text":        "All labels and descriptions shown in white — regardless of theme. Improves readability on dark backgrounds.",
    "lbl_notif_title":        "Check in background",
    "desc_notif":             "Notify about new videos every 24h.",
    "btn_save_close":         "Save & close",

    # Theme names
    "theme_dark_crimson":     "Dark Crimson",
    "theme_dark_ocean":       "Dark Ocean",
    "theme_dark_forest":      "Dark Forest",
    "theme_dark_violet":      "Dark Violet",
    "theme_dark_amber":       "Dark Amber",
    "theme_light_classic":    "Light Classic",
    "theme_high_contrast":    "High Contrast",
    "theme_system_label":     "System",

    # AI panel
    "chat_subtitle":          "Gemini · your videos only",
    "chat_subtitle_ollama":   "Ollama · your videos only",
    "chat_ready":             "ready",
    "chat_note":              "Data never leaves your device",

    # AI provider settings
    "lbl_ai_section":         "AI Assistant",
    "ai_provider_gemini":     "Google Gemini (cloud)",
    "ai_provider_ollama":     "Ollama (local, free)",
    "lbl_ollama_url":         "Ollama URL:",
    "lbl_ollama_model":       "Model:",
    "hint_ollama":            "Ollama must be running locally. Download a model: ollama pull llama3.2",
    "btn_test_ollama":        "🔌 Test connection",
    "chat_no_ollama":         "Cannot connect to Ollama.\n\nMake sure Ollama is installed and running.\nDetails: {error}",
}
