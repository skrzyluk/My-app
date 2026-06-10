# YouTube Notifier

Aplikacja desktopowa dla Windows śledząca nowe filmy z subskrybowanych kanałów YouTube. Działa w tle jako ikona w zasobniku systemowym i powiadamia o nowych filmach natywnym powiadomieniem Windows.

## Funkcje

- Przeglądanie nowych filmów z okresu: Dzisiaj / Tydzień / Miesiąc
- Widok kafelkowy z miniaturami, awatarami kanałów i skróconym opisem
- Boczny panel asystenta AI (Google Gemini) z dostępem do pobranych filmów
- 7 motywów kolorystycznych (5 ciemnych + jasny + wysoki kontrast)
- Przełącznik białych czcionek i 4 rozmiary tekstu
- System tray z menu kontekstowym i toast notifications
- Historia podsumowań (SQLite)
- Obsługa języków: polski / angielski (bez restartu)
- Cache 24h — minimalne zużycie YouTube API quota

## Wymagania

- Windows 10+
- Python 3.11+
- Konto Google z dostępem do YouTube
- Plik `client_secrets.json` (Google Cloud Console — YouTube Data API v3)

## Instalacja

```bash
pip install -r requirements-dev.txt
```

Umieść `client_secrets.json` w `%APPDATA%\YouTubeNotifier\`:

```
C:\Users\<user>\AppData\Roaming\YouTubeNotifier\client_secrets.json
```

## Uruchomienie

```bash
python main.py
```

## Testy

```bash
pytest tests/ --cov=. --cov-report=html
```

## Build (.exe)

```powershell
.\build.ps1
```

Plik wykonywalny: `dist\YouTubeNotifier.exe`

## Bezpieczeństwo

| Co | Gdzie |
|----|-------|
| Refresh token OAuth 2.0 | Windows Credential Manager (keyring) |
| Access token | RAM (tylko sesja) |
| Klucz Gemini API | Windows Credential Manager (keyring) |
| `client_secrets.json` | `%APPDATA%\YouTubeNotifier\` (poza repo) |

Tokeny nie są nigdy zapisywane w plikach ani logach.

## Architektura

```
main.py                  # Entry point: QApplication + system tray
ui/                      # Widgety PyQt6 (okna, dialogi, karty)
services/                # OAuth, YouTube API, Gemini AI, powiadomienia
workers/                 # QThread — sprawdzanie w tle
database/                # SQLite CRUD
models/                  # dataclassy: Video, Summary
config/                  # QSettings (motyw, język, toggle)
i18n/                    # Słowniki PL / EN
resources/               # Ikony, style QSS
```

### YouTube API — flow wywołań

```
subscriptions.list → channels.list (batch) → playlistItems.list (paginacja)
→ videos.list (batch) → filtrowanie po dacie po stronie klienta
```

Szacowane zużycie quota przy 50 subskrypcjach: ~54 j./dzień (limit: 10 000 j.).

## Motywy

| Motyw | Tło | Akcent |
|-------|-----|--------|
| 🌙 Dark Crimson | `#0f0f0f` | `#ff0000` |
| 🌊 Dark Ocean | `#060d1a` | `#0ea5e9` |
| 🌿 Dark Forest | `#071210` | `#22c55e` |
| 🔮 Dark Violet | `#0d0a1a` | `#a855f7` |
| 🌅 Dark Amber | `#0f0c06` | `#f59e0b` |
| ☀️ Light Classic | `#f5f5f5` | `#cc0000` |
| ⬛ High Contrast | `#000000` | `#ffff00` |

## Logi

```
%APPDATA%\YouTubeNotifier\app.log
```

## Licencja

Projekt prywatny — Łukasz Skrzyluk
