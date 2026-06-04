# 🖥️ YouTube Notifier – Specyfikacja Projektu (Windows Desktop)

**Autor:** Łukasz (skrzyluk@gmail.com)  
**Lokalizacja:** Wrocław, Polska  
**Data:** 4 czerwca 2026  
**Status:** Development Plan

---

## 🎯 **1. OVERVIEW**

### Cel Aplikacji
Aplikacja desktopowa dla Windows wyświetlająca **podsumowanie nowych filmów** z subskrybowanych kanałów YouTube w wybranym okresie czasu (Dzisiaj, Tydzień, Miesiąc). Działa w tle jako ikona w zasobniku systemowym i powiadamia o nowych filmach natywnym powiadomieniem Windows.

### Platforma
- **Windows 10+** (aplikacja desktopowa)
- **Dystrybucja:** plik `.exe` (PyInstaller)
- **Bez backendu** – wszystko lokalnie na komputerze użytkownika
- **Przyszłość:** Web app version

### Tech Stack
```
Język:              Python 3.11+
GUI Framework:      PyQt6
State Management:   PyQt6 signals/slots
Local Database:     SQLite (wbudowany sqlite3)
API:                YouTube Data API v3
Autentykacja:       OAuth 2.0 (google-auth-oauthlib)
Bezpieczne hasła:   keyring (Windows Credential Manager)
Powiadomienia:      winotify (Windows toast notifications)
System tray:        QSystemTrayIcon (PyQt6)
Wątek w tle:        QThread (PyQt6)
Build:              PyInstaller → .exe
```

---

## 🔐 **2. AUTENTYKACJA & BEZPIECZEŃSTWO**

### OAuth 2.0 Flow
```
1. Przy pierwszym otwarciu → Login screen
2. Użytkownik klika "Zaloguj przez Google"
3. Otwiera się przeglądarka → Google OAuth consent screen
4. Użytkownik autoryzuje aplikację
5. Aplikacja otrzymuje:
   - access_token (krótkotrwały, w pamięci RAM)
   - refresh_token (długotrwały → Windows Credential Manager)
6. Auto-refresh tokenu gdy wygasł
7. Obsługa revoked token (invalid_grant → ponowny login)
```

### OAuth Scope
```
https://www.googleapis.com/auth/youtube.readonly
```

### Zasady Bezpieczeństwa
- ❌ NIGDY nie przechowuj hasła ani tokenu w pliku tekstowym
- ✅ Refresh token w Windows Credential Manager (keyring)
- ✅ Access token tylko w RAM (sesja)
- ✅ `client_secrets.json` poza repo, w `%APPDATA%\YouTubeNotifier\`
- ✅ Opcja Logout w ustawieniach
- ✅ `.gitignore` obejmuje `client_secrets.json`, `*.token`

### Pakiety
```python
google-auth-oauthlib>=1.2
google-api-python-client>=2.130
keyring>=25.0
```

---

## 📊 **3. FLOW APLIKACJI**

### 3.1 Login Screen
```
┌─────────────────────────────┐
│                             │
│      YOUTUBE NOTIFIER       │
│                             │
│   [Zaloguj się przez Google]│
│                             │
└─────────────────────────────┘
```

**Logika:**
- Sprawdź czy refresh_token istnieje (keyring)
- Jeśli tak → auto-login, otwórz Main Window
- Jeśli nie → pokaż przycisk logowania

---

### 3.2 Main Window (Główne okno)
```
┌─────────────────────────────────────────┐
│ YouTube Notifier          [_][□][X]     │
├─────────────────────────────────────────┤
│  Nowe filmy z:                          │
│  [Dzisiaj]  [Tydzień]  [Miesiąc]        │
├─────────────────────────────────────────┤
│  📺 Filmy (3):           [⟳ Odśwież]   │
│                                         │
│  • Tytuł: "Flutter 3.0 Deep Dive"       │
│    Opis: "W tym filmie omawiamy..."     │
│    Link: https://youtube.com/watch?v=.. │
│    Długość: 45:32                       │
│    Data: 2 cze 2026                     │
│    [📋 Kopiuj] [🔗 Otwórz w YouTube]   │
│                                         │
│  • Tytuł: "..."                         │
│    ...                                  │
│                                         │
├─────────────────────────────────────────┤
│  [📋 Kopiuj wszystko] [⏰ Historia]     │
│                              [⚙ Ustawienia]
└─────────────────────────────────────────┘
```

**Logika:**
1. Pobierz subscriptions → upload playlist IDs → filmy → szczegóły
2. Filtruj po dacie (Dzisiaj/Tydzień/Miesiąc) po stronie klienta
3. Cache 24h w SQLite (zmniejsz zużycie YouTube API quota)
4. Sortuj: newest first
5. Zapisz podsumowanie do historii (SQLite) przy każdym odświeżeniu

---

### 3.3 Settings Dialog
```
┌─────────────────────────────┐
│ Ustawienia              [X] │
├─────────────────────────────┤
│ Język:                      │
│ (●) Polski  ( ) English     │
│                             │
│ Wygląd:                     │
│ ( ) Jasny                   │
│ (●) Ciemny                  │
│ ( ) Systemowy               │
│                             │
│ Powiadomienia w tle:        │
│ [Toggle ON] Sprawdzaj co    │
│ 24h i powiadamiaj           │
│                             │
│           [Wyloguj się]     │
│              [Zamknij]      │
└─────────────────────────────┘
```

---

### 3.4 History Dialog
```
┌─────────────────────────────────────────┐
│ Historia podsumowań             [X]     │
├─────────────────────────────────────────┤
│ [Szukaj...] [Po dacie ↓]                │
├─────────────────────────────────────────┤
│ 5 czerwca 2026  –  Tydzień  (3 filmy)  │
│ • "Flutter 3.0 Deep Dive"  [📋 Kopiuj] │
│                                         │
│ 4 czerwca 2026  –  Dzisiaj  (2 filmy)  │
│ • "Dart Best Practices"    [📋 Kopiuj] │
└─────────────────────────────────────────┘
```

---

### 3.5 System Tray
```
Ikona w zasobniku systemowym (prawy dolny róg)

Klik prawym → menu kontekstowe:
  📺 Otwórz YouTube Notifier
  ⟳  Odśwież teraz
  ────────────────
  ✕  Wyjdź

Dwuklik → przywraca/focusuje okno

Toast notification (gdy nowe filmy):
  ┌─────────────────────────────────┐
  │ 🎬 YouTube Notifier             │
  │ 3 nowe filmy z Twojej listy!   │
  │                       [Otwórz] │
  └─────────────────────────────────┘
```

---

## 📥 **4. FORMAT PODSUMOWANIA**

### Tekst do kopiowania
```
📺 Nowe filmy z ostatniego tygodnia (3 filmy):

• Tytuł: "Flutter 3.0 Deep Dive"
  Opis: "W tym filmie omawiamy najnowsze funkcje..."
  Link: https://youtube.com/watch?v=...
  Długość: 45:32
  Data publikacji: 2 czerwca 2026

• Tytuł: "Dart Best Practices"
  Opis: "Dowiedz się jak pisać bezpieczny kod..."
  Link: https://youtube.com/watch?v=...
  Długość: 32:15
  Data publikacji: 1 czerwca 2026
```

### Akcje
- **📋 Kopiuj** → kopiuje jeden film do schowka (`QApplication.clipboard()`)
- **📋 Kopiuj wszystko** → kopiuje całe podsumowanie
- **🔗 Otwórz w YouTube** → `QDesktopServices.openUrl()`

---

## ⚙️ **5. YOUTUBE API INTEGRACJA**

### 5.1 Poprawny flow wywołań API

```
Krok 1: subscriptions.list
  Parametry: mine=true, maxResults=50
  Paginacja: nextPageToken do wyczerpania
  Zwraca: lista channelId
  Quota: 1 j./request

Krok 2: channels.list
  Parametry: part=contentDetails, id=channelIds (batch, max 50)
  Zwraca: uploadsPlaylistId dla każdego kanału
  Quota: 1 j./request

Krok 3: playlistItems.list
  Parametry: playlistId=uploadsPlaylistId, maxResults=50
  Paginacja: kontynuuj dopóki publishedAt >= cutoff_date
  Filtrowanie dat: po stronie klienta (API nie wspiera publishedAfter)
  Quota: 1 j./request

Krok 4: videos.list
  Parametry: part=snippet,contentDetails, id=videoIds (batch, max 50)
  Zwraca: tytuł, opis, długość (ISO 8601 duration), data
  Quota: 1 j./request
```

### 5.2 Quota Management
```
Daily Limit: 10,000 jednostek

Szacunkowe zużycie (50 subskrypcji, refresh 1x/dzień):
  subscriptions.list:   1 j.
  channels.list:        1 j.
  playlistItems.list:  ~50 j.
  videos.list:         ~2 j. (batch po 50)
  RAZEM:               ~54 j. ✅ (185x poniżej limitu)

Worst case (200 subskrypcji):
  ~204 j. ✅ (nadal bezpieczne)
```

### 5.3 Error Handling
```
1. HTTP 429 (quota exceeded):
   → Pokaż komunikat "Dzienny limit API wyczerpany, spróbuj jutro"
   → Załaduj dane z cache jeśli dostępne

2. HTTP 401 (token wygasł):
   → Auto-refresh access_token z refresh_token
   → Jeśli refresh_token nieważny → pokaż Login screen

3. Brak internetu:
   → Załaduj ostatni cache z SQLite
   → Pokaż info "Dane z cache (brak połączenia)"

4. Inne błędy (4xx, 5xx):
   → Exponential backoff: 1s, 2s, 4s, 8s
   → Po 4 próbach → pokaż Error Dialog z dokładnym komunikatem

Error Dialog:
  "Błąd YouTube API: [exact_error_message]"
  "Kod błędu: [error_code]"
  [Pokaż szczegóły techniczne] [Zamknij]

Log do pliku: %APPDATA%\YouTubeNotifier\app.log
Format: [TIMESTAMP] [LEVEL] [ERROR_CODE] [MESSAGE]
```

---

## 💾 **6. LOCAL DATABASE (SQLite)**

### 6.1 Schema

```sql
-- Cache filmów
CREATE TABLE videos (
    video_id     TEXT PRIMARY KEY,
    channel_id   TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    url          TEXT NOT NULL,
    duration     TEXT,
    published_at TEXT NOT NULL,
    fetched_at   TEXT NOT NULL,
    cached_until TEXT NOT NULL
);

-- Historia podsumowań
CREATE TABLE summaries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period       TEXT NOT NULL,    -- 'today' | 'week' | 'month'
    videos_count INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    created_at   TEXT NOT NULL     -- ISO 8601
);

-- Ustawienia aplikacji
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### 6.2 Caching Strategy
```
1. Przy odświeżeniu → sprawdź cached_until dla każdego kanału
2. Jeśli now < cached_until → użyj danych z bazy (bez API call)
3. Jeśli now > cached_until → pobierz z API, zapisz z cached_until = now + 24h
4. Przycisk "Odśwież" → force refresh (ignoruj cache)
5. Zapis do summaries: przy każdym odświeżeniu
   (sprawdź duplikaty: ten sam dzień + period → nadpisz)
```

---

## 🔔 **7. BACKGROUND WORKER & POWIADOMIENIA**

### 7.1 Background Worker (QThread)
```
- Uruchamia się przy starcie aplikacji (jeśli toggle ON w ustawieniach)
- QTimer co 24h → sprawdź nowe filmy
- Porównaj z ostatnim check: jeśli nowe filmy → wyślij toast
- Działa gdy okno jest zminimalizowane / w tray
- Nie działa gdy aplikacja jest zamknięta (nie jest usługą systemową)
```

### 7.2 Windows Toast Notifications (winotify)
```python
# Powiadomienie o nowych filmach
Tytuł:   "YouTube Notifier"
Treść:   "🎬 {N} nowych filmów z Twojej listy!"
Akcja:   [Otwórz] → przywraca okno aplikacji
```

### 7.3 System Tray (QSystemTrayIcon)
```
- Minimalizacja: przechwycenie closeEvent → chowaj do tray (nie zamykaj)
- Menu kontekstowe: Otwórz / Odśwież / Wyjdź
- Dwuklik: show() + activateWindow()
- Wyjście: tylko przez menu "Wyjdź"
```

---

## 📁 **8. FOLDER STRUCTURE**

```
youtube_notifier/
├── main.py                        # Entry point: QApplication + tray
├── ui/
│   ├── login_window.py            # Login screen
│   ├── main_window.py             # Główne okno
│   ├── settings_dialog.py         # Dialog ustawień
│   └── history_dialog.py          # Dialog historii
├── services/
│   ├── auth_service.py            # OAuth 2.0 + keyring
│   ├── youtube_service.py         # YouTube API calls
│   └── notification_service.py    # winotify wrapper
├── workers/
│   └── background_worker.py       # QThread + QTimer
├── database/
│   └── db.py                      # sqlite3 CRUD wrapper
├── models/
│   ├── video.py                   # dataclass Video
│   └── summary.py                 # dataclass Summary
├── utils/
│   ├── constants.py               # API scopes, timeouts, app paths
│   ├── logger.py                  # logging → %APPDATA%\YouTubeNotifier\app.log
│   └── date_helper.py             # cutoff dates, duration parsing
├── config/
│   └── settings.py                # QSettings wrapper (język, theme, toggle)
├── i18n/
│   ├── pl.py                      # Słownik polski
│   └── en.py                      # English dictionary
├── resources/
│   └── icon.ico                   # Tray + okno icon
├── tests/
│   ├── unit/
│   │   ├── test_youtube_service.py
│   │   ├── test_auth_service.py
│   │   ├── test_db.py
│   │   └── test_date_helper.py
│   ├── integration/
│   │   ├── test_youtube_api.py
│   │   └── test_database.py
│   └── conftest.py                # Fixtures + mock credentials
├── requirements.txt
├── requirements-dev.txt
├── build.spec                     # PyInstaller config
├── CLAUDE.md
└── README.md
```

---

## 🚀 **9. FAZY WDROŻENIA**

### Phase 1: Setup Projektu
- [ ] Struktura folderów
- [ ] `requirements.txt` (wersje pinned)
- [ ] `requirements-dev.txt` (pytest, pytest-cov, pytest-qt, responses)
- [ ] `main.py` – puste okno QApplication
- [ ] `.gitignore` (venv, `__pycache__`, `client_secrets.json`, `*.log`)
- [ ] `CLAUDE.md`

### Phase 2: Autentykacja (OAuth 2.0)
- [ ] `auth_service.py`: authenticate(), get_credentials(), logout()
- [ ] `login_window.py`
- [ ] Zapis/odczyt refresh_token przez keyring
- [ ] Obsługa invalid_grant
- [ ] Testy: `test_auth_service.py`

### Phase 3: YouTube API
- [ ] `youtube_service.py`: wszystkie 4 kroki flow
- [ ] Paginacja z nextPageToken
- [ ] Early stop w playlistItems (data < cutoff)
- [ ] Retry z exponential backoff
- [ ] Testy: `test_youtube_service.py` (mock HTTP via `responses`)

### Phase 4: Baza Danych
- [ ] `db.py`: schema + CRUD
- [ ] Cache strategy (cached_until)
- [ ] Zapis/odczyt summaries (deduplikacja)
- [ ] Testy: `test_db.py`

### Phase 5: Logika Biznesowa
- [ ] `date_helper.py`: cutoff dates, ISO duration → HH:MM:SS
- [ ] Filtrowanie + sortowanie filmów
- [ ] Generowanie tekstu podsumowania
- [ ] Copy to clipboard
- [ ] Testy: `test_date_helper.py`

### Phase 6: UI – Funkcjonalne (bez stylu)
- [ ] `main_window.py`: tabs, lista filmów, przyciski
- [ ] `history_dialog.py`
- [ ] `settings_dialog.py`
- [ ] Nawigacja między oknami
- [ ] `i18n/` + przełączanie języka bez restartu

### Phase 7: System Tray + Powiadomienia
- [ ] `QSystemTrayIcon` w `main.py`
- [ ] `background_worker.py` (QThread + QTimer 24h)
- [ ] `notification_service.py` (winotify)
- [ ] Minimalizacja do tray (closeEvent override)
- [ ] Testy: `test_background_worker.py`

### Phase 8: Ustawienia + Theme
- [ ] `config/settings.py` (QSettings)
- [ ] Light/Dark/System theme (QPalette)
- [ ] Lokalizacja PL/EN
- [ ] Logout

### Phase 9: Frontend Design *(do zaprojektowania osobno)*
- [ ] Styl wizualny – TBD
- [ ] Custom QSS stylesheet
- [ ] Własne widgety (VideoCard, SummaryCard)
- [ ] Animacje (loading spinner, fade in)
- [ ] Ikony i branding

### Phase 10: Testy + Polish
- [ ] `pytest --cov` → ≥80% coverage
- [ ] Error handling + error dialog
- [ ] Logger → `%APPDATA%\YouTubeNotifier\app.log`
- [ ] Edge cases: brak internetu, 0 subskrypcji, quota exceeded

### Phase 11: Build & Dystrybucja
- [ ] `build.spec` (PyInstaller, one-dir)
- [ ] Test `.exe` na czystym Windows 10 (bez Pythona)
- [ ] Opcjonalnie: Inno Setup installer

---

## 🧪 **10. TESTING STRATEGY**

### Coverage Target: ≥80%

### Struktura testów
```
tests/
├── unit/           # logika biznesowa, serwisy, baza
├── integration/    # prawdziwe API calls (wymaga credentials)
└── conftest.py     # mock OAuth, mock YouTube responses, temp SQLite
```

### Kluczowe scenariusze
```
✅ OAuth login / logout / auto-refresh / invalid_grant
✅ Pobranie subskrypcji z paginacją
✅ Pobranie filmów + filtrowanie po dacie
✅ Cache hit / miss / force refresh
✅ Error handling (429, 401, brak internetu)
✅ CRUD bazy danych
✅ Zapis summaries (deduplikacja)
✅ Background worker (mock QTimer)
✅ Settings persistence
✅ Przełączanie języka
✅ Copy to clipboard
```

---

## 📋 **11. DONE CHECKLIST**

Przed release:
- [ ] Wszystkie testy pass (≥80% coverage)
- [ ] Error handling kompleksowy
- [ ] Logger działa (`%APPDATA%\YouTubeNotifier\app.log`)
- [ ] `client_secrets.json` poza repo
- [ ] `.exe` builduje się bez błędów
- [ ] Działa na czystym Windows 10+ (bez Pythona)
- [ ] System tray działa poprawnie
- [ ] Toast notifications działają
- [ ] Code review done

---

**Status:** ✅ Specyfikacja gotowa do development  
**Ostatnia aktualizacja:** 4 czerwca 2026  
**Platforma:** Windows 10+ Desktop (Python + PyQt6)
