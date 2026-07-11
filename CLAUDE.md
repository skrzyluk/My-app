# YouTube Notifier – Instrukcje dla Claude Code

## Projekt
Aplikacja desktopowa Windows (Python 3.11 + PyQt6) do śledzenia nowych filmów z subskrybowanych kanałów YouTube.

Pełna specyfikacja: `PROJECT_SPEC.md`

## Stack
- **GUI:** PyQt6 (signals/slots, QThread, QSystemTrayIcon)
- **Auth:** google-auth-oauthlib + keyring (Windows Credential Manager)
- **API:** google-api-python-client (YouTube Data API v3)
- **AI chat:** lokalny model przez **Ollama** (`POST /api/chat`) – boczny panel asystenta nad listą filmów (`ui/ai_chat_widget.py`, `services/ai_service.py`). Domyślnie `llama3.2:3b`. Renderowanie odpowiedzi (klikalne linki, Markdown): `utils/chat_render.py`
- **DB:** SQLite (wbudowany sqlite3)
- **Powiadomienia:** winotify (Windows toast)
- **Motywy:** silnik tokenów QSS w `resources/styles.py` – 7 motywów + białe czcionki + skala czcionki
- **Testy:** pytest + pytest-qt + responses
- **Build:** PyInstaller

## Zasady pisania kodu

1. **State management** przez PyQt6 signals/slots – nie używaj globalnych zmiennych
2. **Każdy serwis** ma odpowiadający plik testów w `tests/unit/`
3. **Error handling** – każde wywołanie API opakowane w try/except z logowaniem
4. **Quota YouTube API** – zawsze sprawdzaj cache przed wywołaniem API
5. **Tokeny** – nigdy nie loguj access_token, refresh_token ani żadnych kluczy API
6. **Nowy ekran** = nowy plik w `ui/` + widget testy w `tests/unit/`
7. **Style** – nie zaszywaj kolorów w widgetach; używaj `objectName`/property + tokenów motywu w `resources/styles.py`. Motyw aplikuje się przez `config.theme.apply_theme(app, theme, white_text=, font_scale=)`.

## YouTube API – poprawny flow wywołań
```
subscriptions.list → channels.list (batch) → playlistItems.list (paginacja + early stop) → videos.list (batch)
```
Filtrowanie dat po stronie klienta – NIE używaj publishedAfter w playlistItems.list (nie istnieje).

## Fazy wdrożenia
- **Phase 1** ✅ Setup projektu
- **Phase 2** – Autentykacja OAuth 2.0
- **Phase 3** – YouTube API
- **Phase 4** – Baza danych SQLite
- **Phase 5** – Logika biznesowa
- **Phase 6** – UI (funkcjonalne)
- **Phase 7** – System tray + powiadomienia
- **Phase 8** – Ustawienia + lokalizacja
- **Phase 9** ✅ Frontend design – wg `mockup-final-v4.html` (widok kafelkowy, 7 motywów, białe czcionki, rozmiar tekstu, boczny panel AI). Decyzje: `DESIGN_DECISIONS.md`
- **Phase 10** – Testy + polish
- **Phase 11** ✅ Build .exe (one-file; `client_secrets.json` czytany z `%APPDATA%`, nie wbudowany)
- **Phase 12** ✅ Lista: status „obejrzane" + licznik, filtry (kanał, „tylko nieobejrzane") i sortowanie (data/długość). Czat: klikalne linki/tytuły, Markdown, kopiowanie, „Nowy czat"

## Asystent AI (Ollama)
- Inferencja **lokalna** przez Ollama – brak klucza w chmurze, dane nie opuszczają urządzenia
- Model, adres, `num_gpu`, `temperature` konfigurowalne (`config/settings.py`; UI: adres + model w Ustawieniach). Domyślnie `llama3.2:3b`, temp 0.1, pełny GPU
- Asystent ma dostęp **wyłącznie do pobranych filmów** (kontekst + guardrail „funkcja-first" budowany w `services/ai_service.py`). Nie rozbudowuj promptu w celu twardszego blokowania off-topic – to psuje działanie na modelu 3B
- Setup: `ollama pull llama3.2:3b`

## Build .exe
```bash
# buduj przez venv (systemowy python nie ma zależności)
.\venv\Scripts\python.exe -m PyInstaller build.spec --clean --noconfirm
```
Po zmianach wpływających na runtime przebudowuj `dist\YouTubeNotifier.exe`.

## Uruchomienie
```bash
pip install -r requirements-dev.txt
python main.py
```

## Testy
```bash
pytest tests/ --cov=. --cov-report=html
```

## Ważne ścieżki
- Logi: `%APPDATA%\YouTubeNotifier\app.log`
- Secrets: `%APPDATA%\YouTubeNotifier\client_secrets.json`
- Token: Windows Credential Manager (keyring) – NIE w plikach
