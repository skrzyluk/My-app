# YouTube Notifier

Aplikacja desktopowa dla Windows śledząca nowe filmy z subskrybowanych kanałów YouTube. Działa w tle jako ikona w zasobniku systemowym i powiadamia o nowych filmach natywnym powiadomieniem Windows.

## Funkcje

- Przeglądanie nowych filmów z okresu: Dzisiaj / Tydzień / Miesiąc
- Widok kafelkowy z miniaturami, awatarami kanałów i skróconym opisem
- **Status „obejrzane"** — oznaczanie filmów jako obejrzane (przygaszenie karty) i licznik nieobejrzanych
- **Filtry i sortowanie** — po kanale, „tylko nieobejrzane", sortowanie: Najnowsze / Najstarsze / Najdłuższe / Najkrótsze
- Wyszukiwarka filmów na żywo
- **Lokalny asystent AI (Ollama)** rozmawiający wyłącznie o pobranych filmach — dane nie opuszczają urządzenia
- 7 motywów kolorystycznych (5 ciemnych + jasny + wysoki kontrast)
- Przełącznik białych czcionek i 4 rozmiary tekstu
- System tray z menu kontekstowym i toast notifications
- Historia podsumowań (SQLite)
- Obsługa języków: polski / angielski (bez restartu)
- Automatyczne logowanie — przy zapisanej sesji aplikacja pomija ekran logowania i od razu otwiera główne okno
- Cache 24h — minimalne zużycie YouTube API quota

## Wymagania

- Windows 10+
- Python 3.11+
- Konto Google z dostępem do YouTube
- Plik `client_secrets.json` (Google Cloud Console — YouTube Data API v3)
- **Do panelu AI (opcjonalnie):** [Ollama](https://ollama.com) uruchomione lokalnie oraz pobrany model:
  ```
  ollama pull llama3.2:3b
  ```

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

Przy pierwszym uruchomieniu zaloguj się przez OAuth. Przy kolejnych — jeśli sesja jest zapisana — aplikacja loguje się automatycznie i pomija ekran logowania.

## Lista filmów — obejrzane, filtry, sortowanie

- **Obejrzane** — przycisk „✓ Obejrzane / ↺ Nieobejrzane" na każdej karcie. Obejrzane filmy są przygaszone, a flaga jest zapisywana w bazie i **przetrwa odświeżenie** listy. Toolbar pokazuje licznik nieobejrzanych (np. „📺 12 filmów · 3 nieobejrz.").
- **Filtr kanału** — lista rozwijana z kanałami bieżących filmów.
- **Tylko nieobejrzane** — checkbox ukrywający obejrzane.
- **Sortowanie** — Najnowsze / Najstarsze / Najdłuższe / Najkrótsze.
- **Wyszukiwarka** — filtrowanie po tytule, kanale i opisie na żywo.

Wszystkie filtry działają łącznie (wyszukiwarka + kanał + „tylko nieobejrzane" + sortowanie).

## Panel AI (Ollama)

Boczny asystent, który **rozmawia wyłącznie o pobranych filmach** — analizuje, poleca, streszcza i filtruje listę po temacie. Cała inferencja odbywa się **lokalnie przez Ollama**; dane nie opuszczają urządzenia i nie jest potrzebny żaden klucz API w chmurze.

Funkcje czatu:
- **Klikalne linki** do filmów i klikalne tytuły filmów z listy
- **Formatowanie Markdown** (pogrubienie, kursywa, `kod`, listy)
- **Kopiowanie odpowiedzi** i przycisk **„Nowy czat"** (reset rozmowy)
- Szybkie podpowiedzi (np. „Podsumuj wszystkie filmy", „Co polecasz obejrzeć?")

Konfiguracja w **Ustawieniach** (adres Ollama, model). Domyślnie: model `llama3.2:3b`, pełny offload na GPU, niska temperatura (trzymanie się listy filmów). Parametry `ollama_model`, `ollama_num_gpu`, `ollama_temperature` są konfigurowalne.

## Testy

```bash
pytest tests/ --cov=. --cov-report=html
```

## Build (.exe)

```powershell
.\venv\Scripts\python.exe -m PyInstaller build.spec --clean --noconfirm
```

(Skrypt `.\build.ps1` również działa, ale używa `python` z PATH — jeśli zależności są w wirtualnym środowisku, buduj przez `venv` jak wyżej.)

Plik wykonywalny: `dist\YouTubeNotifier.exe` (one-file, ~58 MB, bez okna konsoli).

`client_secrets.json` **nie jest wbudowywany** w exe — aplikacja czyta go w czasie działania z `%APPDATA%\YouTubeNotifier\`. Na docelowym komputerze umieść tam ten plik przed pierwszym uruchomieniem.

## Bezpieczeństwo

| Co | Gdzie |
|----|-------|
| Refresh token OAuth 2.0 | Windows Credential Manager (keyring) |
| Access token | RAM (tylko sesja) |
| Asystent AI | Lokalnie (Ollama) — dane nie opuszczają urządzenia, brak klucza w chmurze |
| `client_secrets.json` | `%APPDATA%\YouTubeNotifier\` (poza repo, nie wbudowany w exe) |

Tokeny nie są nigdy zapisywane w plikach ani logach.

## Architektura

```
main.py                  # Entry point: QApplication + system tray
ui/                      # Widgety PyQt6 (okna, dialogi, karty, panel AI)
services/                # OAuth, YouTube API, AI (Ollama), powiadomienia
workers/                 # QThread — sprawdzanie w tle
database/                # SQLite CRUD (m.in. stan „obejrzane")
models/                  # dataclassy: Video, Summary
config/                  # QSettings (motyw, język, model AI, toggle)
i18n/                    # Słowniki PL / EN
resources/               # Ikony, style QSS
utils/                   # Pomocnicze: renderowanie czatu, daty, logi
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

Projekt prywatny — Skrzyluk
