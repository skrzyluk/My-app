# YouTube Notifier – Instrukcje dla Claude Code

## Projekt
Aplikacja desktopowa Windows (Python 3.11 + PyQt6) do śledzenia nowych filmów z subskrybowanych kanałów YouTube.

Pełna specyfikacja: `PROJECT_SPEC.md`

## Stack
- **GUI:** PyQt6 (signals/slots, QThread, QSystemTrayIcon)
- **Auth:** google-auth-oauthlib + keyring (Windows Credential Manager)
- **API:** google-api-python-client (YouTube Data API v3)
- **DB:** SQLite (wbudowany sqlite3)
- **Powiadomienia:** winotify (Windows toast)
- **Testy:** pytest + pytest-qt + responses
- **Build:** PyInstaller

## Zasady pisania kodu

1. **State management** przez PyQt6 signals/slots – nie używaj globalnych zmiennych
2. **Każdy serwis** ma odpowiadający plik testów w `tests/unit/`
3. **Error handling** – każde wywołanie API opakowane w try/except z logowaniem
4. **Quota YouTube API** – zawsze sprawdzaj cache przed wywołaniem API
5. **Tokeny** – nigdy nie loguj access_token ani refresh_token
6. **Nowy ekran** = nowy plik w `ui/` + widget testy w `tests/unit/`

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
- **Phase 9** – Frontend design (TBD)
- **Phase 10** – Testy + polish
- **Phase 11** – Build .exe

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
