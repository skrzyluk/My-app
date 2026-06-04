# 📱 YouTube Notifier - Specyfikacja Projektu

**Autor:** Łukasz (skrzyluk@gmail.com)  
**Lokalizacja:** Wrocław, Polska  
**Data:** 4 czerwca 2026  
**Status:** Development Plan

---

## 🎯 **1. OVERVIEW**

### Cel Aplikacji
Mobilna aplikacja Flutter wyświetlająca **podsumowanie nowych filmów** z subskrybowanych kanałów YouTube w wybranym okresie czasu (Dzisiaj, Tydzień, Miesiąc).

### Platforma
- **Tylko Flutter app** (bez backendu)
- **Android 10+** (internal testing)
- **Instalacja:** Zewnętrzne źródło (APK)
- **Przyszłość:** Web app version, Notyfikacje push

### Tech Stack
```
Framework:        Flutter 3.20+
Language:         Dart
State Management: Provider
Local Database:   SQLite (Drift ORM)
API:              YouTube Data API v3
Authentication:   OAuth 2.0
Caching:          24 godziny
Push (Future):    Firebase Cloud Messaging (FCM)
```

---

## 🔐 **2. AUTENTYKACJA & BEZPIECZEŃSTWO**

### OAuth 2.0 Flow
```
1. Przy pierwszym otwarciu → Redirect na YouTube Login
2. Użytkownik autoryzuje aplikację
3. Aplikacja otrzymuje:
   - access_token (krótkotrwały)
   - refresh_token (długotrwały - SECURE STORAGE)
4. Refresh token przechowywany w:
   - iOS: Keychain
   - Android: EncryptedSharedPreferences
5. Auto-refresh tokenu gdy wygasł
```

### ⚠️ Zasady Bezpieczeństwa
- ❌ NIGDY nie przechowywuj hasła w pamięci
- ✅ Refresh token w Secure Storage
- ✅ Access token w sesji (RAM)
- ✅ Opcja Logout w ustawieniach

### Pakiety
```dart
flutter_secure_storage
google_sign_in
googleapis
```

---

## 📊 **3. FLOW APLIKACJI**

### 3.1 Splash/Login Screen
```
┌─────────────────────┐
│   YOUTUBE NOTIFIER  │
│                     │
│  [Zaloguj się]      │
│  Google OAuth       │
└─────────────────────┘
```

**Logika:**
- Sprawdź czy refresh_token istnieje (Secure Storage)
- Jeśli tak → auto-login, przejdź do Home
- Jeśli nie → pokaż button logowania

---

### 3.2 Home Screen (Główny ekran)
```
┌──────────────────────┐
│ ← Settings  [⚙️]     │
├──────────────────────┤
│ Nowe filmy z:        │
│ [Dzisiaj][Tydzień][Miesiąc]
├──────────────────────┤
│ 📺 Filmy (3):        │
│                      │
│ • Tytuł: "..."       │
│   Opis: "..."        │
│   Link: [youtube...] │
│   Długość: 45:32     │
│   Data: 2 cze 2026   │
│   [📋 Copy] [📤 Share]
│                      │
│ • Tytuł: "..."       │
│   ...                │
│                      │
│ [⏰ History]         │
└──────────────────────┘
```

**Logika:**
1. Pobierz subscriptions (kanały które obserwujesz)
2. Dla każdego kanału → pobierz playlistItems (filmy)
3. Filtruj po dacie (Dzisiaj/Tydzień/Miesiąc)
4. Cache 24h (zmniejsz YouTube API quota)
5. Sortuj: newest first
6. Wyświetl listę punktowaną

---

### 3.3 Settings Screen
```
┌──────────────────────┐
│ ← Ustawienia         │
├──────────────────────┤
│ Język:               │
│ [ ] Polski  [✓]      │
│ [ ] English          │
│                      │
│ Wygląd:              │
│ [ ] Light            │
│ [ ] Dark    [✓]      │
│ [ ] System default   │
│                      │
│ Push Notifications:  │
│ [Toggle ON/OFF] ✓    │
│ Sprawdzaj co 24h     │
│ (przy wyłączeniu)    │
│                      │
│ [Wyloguj się]        │
└──────────────────────┘
```

**Ustawienia:**
- Język interfejsu: PL / ENG
- Theme: Light / Dark / System
- Push notifications: Toggle + info

---

### 3.4 History Screen
```
┌──────────────────────┐
│ ← Historia           │
├──────────────────────┤
│ Szukaj / Filtruj     │
│ [Po dacie ↓]         │
│                      │
│ 5 czerwca:  (3 nowe) │
│ • Tytuł: "..." [📋]  │
│                      │
│ 4 czerwca:  (2 nowe) │
│ • Tytuł: "..." [📋]  │
│                      │
│ 3 czerwca:  (5 nowych)
│ • Tytuł: "..." [📋]  │
└──────────────────────┘
```

**Logika:**
- Wyświetl historię podsumowań z bazy danych (SQLite)
- Sorting: po dacie (newest first)
- Copy do schowka, Share na WhatsApp/Messenger

---

## 📥 **4. PODSUMOWANIE - Format**

### Struktura Listy Punktowanej
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

• Tytuł: "Provider State Management"
  Opis: "Kompleksowy poradnik Provider pattern..."
  Link: https://youtube.com/watch?v=...
  Długość: 58:42
  Data publikacji: 31 maja 2026
```

### Akcje na Podsumowaniu
- **📋 Copy** → Skopiuj całe podsumowanie do schowka
- **📤 Share** → Udostępnij na WhatsApp, Messenger
- **🔗 Link** → Otwórz film w YouTube app

---

## ⚙️ **5. YOUTUBE API INTEGRACJA**

### 5.1 Endpoints
```
1. subscriptions.list
   Parametry: mine=true, maxResults=50
   Zwraca: Listę kanałów subskrybowanych
   Quota: ~100 jednostek

2. playlistItems.list
   Parametry: playlistId, maxResults=50, publishedAfter
   Zwraca: Filmy z kanału (z upload playlist)
   Quota: ~1 jednostka/request

3. videos.list
   Parametry: videoId, part=snippet,contentDetails
   Zwraca: Detale filmu (opis, długość, etc)
   Quota: ~1 jednostka/request
```

### 5.2 Quota Management
```
Daily Limit: 10,000 jednostek
Szacunkowe zużycie na dzień: ~250 jednostek

Kalkulacja:
- subscriptions.list:     100 j.
- 10x playlistItems:      100 j.
- 50x videos.list:         50 j.
RAZEM:                    250 j. ✅ (40x poniżej limitu)
```

### 5.3 Error Handling
Jeśli błąd:
```
1. Wyświetl ERROR SCREEN z dokładnym komunikatem:
   "Błąd YouTube API: [exact_error_message]"
   "Kod błędu: [error_code]"

2. Log do lokalnego pliku:
   /data/app.logs
   Format: [TIMESTAMP] [ERROR_CODE] [MESSAGE] [STACK_TRACE]

3. Opcja "Show Error Details" dla developera
   Wskaż dokładnie gdzie w kodzie błąd

4. Auto-retry z exponential backoff
   (Po 1s, 2s, 4s, 8s)
```

---

## 💾 **6. LOCAL DATABASE (SQLite + Drift)**

### 6.1 Tabele

#### `summaries` (Historia podsumowań)
```
id              INTEGER PRIMARY KEY
date_created    DATETIME
period          TEXT (Dzisiaj/Tydzień/Miesiąc)
videos_count    INTEGER
summary_text    TEXT (JSON lub plain text)
created_at      DATETIME
```

#### `videos` (Cache filmów)
```
id              TEXT PRIMARY KEY (videoId z YouTube)
channel_id      TEXT
title           TEXT
description     TEXT
url             TEXT
duration        TEXT (HH:MM:SS)
published_at    DATETIME
fetched_at      DATETIME
cached_until    DATETIME (cache 24h)
```

#### `app_settings` (Ustawienia użytkownika)
```
key             TEXT PRIMARY KEY
value           TEXT
```

### 6.2 Caching Strategy
```
1. Pobierz dane z YouTube API
2. Zapisz w SQLite z timestamp: cached_until = now + 24h
3. Następne żądanie:
   - Jeśli now < cached_until → zwróć z bazy
   - Jeśli now > cached_until → pobierz z API (refresh)
4. Pull-to-refresh → force refresh (skip cache)
```

---

## 🔔 **7. PUSH NOTIFICATIONS (Future Feature)**

### 7.1 Firebase Cloud Messaging (FCM)
```
1. Włączyć FCM w Firebase Console
2. Konfiguracja:
   - google-services.json (Android)
   - GoogleService-Info.plist (iOS)

3. Background Job:
   - Sprawdź nowe filmy co ~24h
   - Jeśli nowe filmy → wyślij notyfikację

4. Notyfikacja:
   "🎬 3 nowe filmy z Twojej listy!"
   [Otwórz]

5. Ustawienie:
   Settings → Push Notifications: [Toggle ON/OFF]
   Jeśli OFF → nie sprawdzaj nowych filmów
```

### 7.2 Local Notifications (Alternative)
```
Jeśli użytkownik wyłączy FCM:
- Notyfikacje wyłączone
- Aplikacja NOT sprawdza nowych filmów
- Użytkownik sami otwiera app aby zobaczyć podsumowanie
```

---

## 🧪 **8. TESTING STRATEGY**

### 8.1 Coverage Target
```
Minimum: 80% code coverage
Testy obejmują:
- Unit tests (logika biznesowa)
- Widget tests (UI)
- Integration tests (API, database)
```

### 8.2 Test Structure
```
test/
├── unit/
│   ├── models_test.dart
│   ├── services_test.dart
│   └── providers_test.dart
├── widget/
│   ├── screens_test.dart
│   └── widgets_test.dart
└── integration/
    ├── youtube_api_test.dart
    └── database_test.dart
```

### 8.3 Key Test Scenarios
```
✅ OAuth Login/Logout
✅ Fetch subscriptions
✅ Fetch videos + filtering
✅ Cache hit/miss
✅ Error handling (API errors)
✅ Database operations (CRUD)
✅ Settings persistence
✅ UI navigation
✅ Dark mode toggle
✅ Language switching
```

---

## 📁 **9. FOLDER STRUCTURE**

```
youtube_notifier/
├── android/               # Android native (gradle config)
├── ios/                  # iOS native (podfile config)
├── lib/
│   ├── main.dart         # Entry point
│   ├── models/
│   │   ├── video.dart
│   │   ├── subscription.dart
│   │   └── summary.dart
│   ├── screens/
│   │   ├── splash_screen.dart
│   │   ├── home_screen.dart
│   │   ├── settings_screen.dart
│   │   └── history_screen.dart
│   ├── services/
│   │   ├── youtube_service.dart
│   │   ├── auth_service.dart
│   │   └── database_service.dart
│   ├── providers/
│   │   ├── auth_provider.dart
│   │   ├── videos_provider.dart
│   │   ├── settings_provider.dart
│   │   └── theme_provider.dart
│   ├── widgets/
│   │   ├── video_card.dart
│   │   ├── summary_card.dart
│   │   └── error_widget.dart
│   ├── utils/
│   │   ├── constants.dart
│   │   ├── logger.dart
│   │   └── date_helper.dart
│   ├── config/
│   │   ├── theme.dart
│   │   └── localization.dart
│   └── database/
│       └── app_database.dart  (Drift config)
├── test/                 # Testy
├── pubspec.yaml         # Dependencies
└── README.md
```

---

## 📝 **10. CLAUDE CODE INTEGRATION**

### 10.1 CLAUDE.md (Instrukcje dla Claude)
```markdown
## For Claude Code:

### Workflow
1. Czytaj PROJECT_SPEC.md najpierw
2. Kiedy piszesz nowy kod:
   - Użyj Provider dla state management
   - Dodaj unit testy (min. 80% coverage)
   - Follow Material Design 3
   - Dodaj error handling z logowaniem

3. Kiedy integrujesz YouTube API:
   - Sprawdź quota w YouTube API Dashboard
   - Dodaj caching (24h)
   - Implementuj retry logic
   - Test z real credentials

4. Kiedy dodajesz nowy ekran:
   - Utwórz screen + provider
   - Dodaj widget tests
   - Update FEATURES.md
   - Zaktualizuj navigation

### Common Tasks
/test {feature}      → Generuj unit testy
/review {file}       → Review kodu
/doc {service}       → Generuj API doc
/quota               → Sprawdź YouTube quota
/error {message}     → Debug błędu
```

---

## 🚀 **11. DEVELOPMENT PHASES**

### Phase 1: Setup & Authentication
- [ ] Projekt Flutter + dependencies
- [ ] OAuth 2.0 + Google Sign-In
- [ ] Secure Storage (Refresh token)
- [ ] Splash + Login screens

### Phase 2: YouTube API Integration
- [ ] Fetch subscriptions
- [ ] Fetch videos per subscription
- [ ] Caching layer (SQLite)
- [ ] Error handling

### Phase 3: Core Features
- [ ] Home screen + summary rendering
- [ ] Date filtering (Today/Week/Month)
- [ ] Copy to clipboard
- [ ] Share (WhatsApp/Messenger)

### Phase 4: Database & History
- [ ] SQLite + Drift setup
- [ ] History persistence
- [ ] History screen UI

### Phase 5: Settings & Localization
- [ ] Theme toggle (Light/Dark/System)
- [ ] Language settings (PL/ENG)
- [ ] Push notifications toggle
- [ ] Logout

### Phase 6: Testing & Polish
- [ ] Unit tests (80%+ coverage)
- [ ] Widget & integration tests
- [ ] Error handling & logging
- [ ] Performance optimization

### Phase 7: Future Features (Roadmap)
- [ ] Firebase Cloud Messaging
- [ ] Push notifications background job
- [ ] Web app version
- [ ] Analytics

---

## 📋 **12. DONE CHECKLIST**

Przed release:
- [ ] Wszystkie testy pass (80%+ coverage)
- [ ] Error handling comprehensive
- [ ] Logging działające
- [ ] Documentation kompletna
- [ ] Code review done
- [ ] Performance tested
- [ ] Security audit passed
- [ ] APK builds successfully
- [ ] Tested na Android 10+

---

## 🔗 **13. HELPFUL RESOURCES**

- [YouTube API Docs](https://developers.google.com/youtube/v3)
- [Flutter Docs](https://flutter.dev/docs)
- [Provider Package](https://pub.dev/packages/provider)
- [Drift ORM](https://drift.simonbinder.eu/)
- [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- [Firebase FCM](https://firebase.google.com/docs/cloud-messaging)

---

**Status:** ✅ Specyfikacja gotowa do development  
**Ostatnia aktualizacja:** 4 czerwca 2026  
**Gotowy do Claude Code?** TAK ✅
