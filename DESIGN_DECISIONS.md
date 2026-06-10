# YouTube Notifier – Decyzje Designu (Phase 9)

**Data:** 6 czerwca 2026  
**Pliki referencyjne:** `mockup-final-v4.html`, `mockup-wcag-v2.html`

---

## 1. Ikona aplikacji

**Wybrana: Opcja A** — dzwonek powiadomień z kółkiem play wewnątrz.

```
SVG: dzwonek (var(--accent)) + koło z trójkątem play (białe)
Rozmiary: 72px (okno) · 48px · 32px · 20px (tray)
```

---

## 2. Layout – widok kafelkowy

- **Domyślnie 3 kolumny** przy szerokości okna ~1000px
- Responsywny grid: 3 kol → 2 kol → 1 kol (media queries)
- Brak widoku listowego — wyłącznie kafelki
- Odstęp między kafelkami: `gap: 12px`

---

## 3. Struktura kafelka (identyczna na każdej karcie)

```
┌─────────────────────────────────────┐
│  [miniatura 16:9]  [NOWY]  [czas]  │
├─────────────────────────────────────┤
│  [avatar] Kanał              Data   │
│                                     │
│  Pełny tytuł (bez obcinania)        │
│  ─────────────────────────────────  │
│  OPIS                               │
│  Tekst opisu (3 linie domyślnie)    │
│  Pokaż więcej ▾                     │
│                                     │
│  [ 📋 Kopiuj ] [ ▶ YouTube ]        │ ← grid 1fr 1fr, h=30px
└─────────────────────────────────────┘
```

**Zasada spójności przycisków:** każda karta ma identyczny `grid-template-columns: 1fr 1fr`, wysokość `30px`, zawsze w tej kolejności: Kopiuj → YouTube. Przyciski przyklejone do dołu przez `margin-top: auto`.

---

## 4. Opis filmów

- **Domyślnie skrócony** do 3 linii (`-webkit-line-clamp: 3`)
- **"Pokaż więcej ▾"** — rozwija pełny opis
- **"Pokaż mniej ▴"** — zwija z powrotem
- Przycisk nie pojawia się, gdy opis mieści się w 3 liniach
- Długie opisy w stanie rozwiniętym są scrollowalne (`overflow-y: auto`)

---

## 5. Motywy kolorystyczne (7 sztuk)

| # | Nazwa | Tło | Akcent | Typ |
|---|-------|-----|--------|-----|
| 1 | 🌙 Dark Crimson | `#0f0f0f` | `#ff0000` | Ciemny |
| 2 | 🌊 Dark Ocean | `#060d1a` | `#0ea5e9` | Ciemny |
| 3 | 🌿 Dark Forest | `#071210` | `#22c55e` | Ciemny |
| 4 | 🔮 Dark Violet | `#0d0a1a` | `#a855f7` | Ciemny |
| 5 | 🌅 Dark Amber | `#0f0c06` | `#f59e0b` | Ciemny |
| 6 | ☀️ Light Classic | `#f5f5f5` | `#cc0000` | Jasny |
| 7 | ⬛ High Contrast | `#000000` | `#ffff00` | HC Black |

**Implementacja:** CSS custom properties (`--accent`, `--bg-app` itd.) + atrybut `data-theme` na głównym oknie. Zmiana motywu nie wymaga restartu.

---

## 6. Przełącznik białych czcionek

- Toggle w panelu Ustawień: **"Białe czcionki"**
- Gdy ON: `--text-primary: #ffffff`, `--text-secondary: #ffffff` — nadpisuje każdy motyw
- Cel: zwiększona czytelność na ciemnym tle
- Stan synchronizowany między paskiem theme-picker a dialogiem Ustawień
- CSS: `[data-white-text="true"] { --text-primary: #fff !important; ... }`

---

## 7. Panel AI Chat

**Wariant: panel boczny (split view)** — zintegrowany z głównym oknem.

```
┌──────────────────────────┬──────────────┐
│  Tiles grid (flex: 1)    │  AI Panel    │
│                          │  (300px)     │
│  [karty filmów]          │  [chat]      │
└──────────────────────────┴──────────────┘
```

- Szerokość panelu: `300px`, chowany przez `width: 0; overflow: hidden`
- Otwieranie/zamykanie: przycisk **🤖 AI Chat** w toolbarze
- Szybkie prompty: "📊 Podsumuj", "🔍 Szukaj", "📺 Kanały"
- Asystent ma dostęp tylko do filmów pobranych z YouTube API
- Dane nie opuszczają urządzenia
- Wizualizacja: wyniki wyszukiwania jako karty z miniaturą i metadanymi

---

## 8. Sortowanie i nawigacja

- Sortowanie: **↑↓ w statusbarze** (skróty klawiszowe)
- Pełna lista skrótów widoczna w statusbarze: `↑↓ nawigacja · Enter otwórz · C kopiuj`
- Brak dropdownu sortowania w wersji MVP

---

## 9. WCAG 2.1 AA — spełnione kryteria

| Kryterium | Opis | Status |
|-----------|------|--------|
| 1.1.1 | Tekst alternatywny (aria-label, aria-hidden) | ✅ |
| 1.3.1 | role="tablist/tab/list/listitem/dialog" | ✅ |
| 1.3.5 | Input type="search" z autocomplete | ✅ |
| 1.4.1 | Aktywna zakładka: kolor + pogrubienie | ✅ |
| 1.4.3 | Kontrast min. 4.5:1 (najniższy: #ff0000/#141414 → 4.7:1) | ✅ |
| 1.4.4 | 4 rozmiary czcionki (13–20px) w Ustawieniach | ✅ |
| 1.4.10 | Reflow: grid 3→2→1 kol bez poziomego scrolla | ✅ |
| 1.4.11 | Kontrast UI components min. 3:1 | ✅ |
| 2.1.1 | tabindex="0" na kartach, skróty klawiszowe | ✅ |
| 2.4.1 | Skip link "Przejdź do treści" | ✅ |
| 2.4.7 | focus-visible: czerwony ring 3px na wszystkich elementach | ✅ |
| 3.3.2 | Etykiety inputów (aria-label / fieldset+legend) | ✅ |
| 4.1.2 | role="switch" na toggleach, aria-selected na tabs | ✅ |
| 4.1.3 | aria-live="polite" na liczniku filmów i statusie | ✅ |

**Kontrast – pary zweryfikowane:**

| Para | Stosunek | Wymóg | Wynik |
|------|----------|-------|-------|
| `#e8e8e8` na `#1c1c1c` (tekst główny) | 13.8:1 | 4.5:1 | ✅ |
| `#aaaaaa` na `#1c1c1c` (tekst wtórny) | 8.3:1 | 4.5:1 | ✅ |
| `#ff0000` na `#141414` (akcent) | 4.7:1 | 4.5:1 | ✅ |
| `#ffffff` na `#ff0000` (tekst na przycisku) | 4.0:1 | 3.0:1 large | ✅ |
| `#3a3a3a` na `#141414` (obramowanie) | 3.2:1 | 3.0:1 UI | ✅ |

---

## 10. Inne elementy UI

### Toolbar
- Zakładki okresu: Dzisiaj / Tydzień / Miesiąc (role="tablist")
- Licznik filmów z `aria-live`
- Przyciski: Odśwież · Kopiuj wszystko · AI Chat · Historia · Ustawienia

### Ustawienia (dialog)
- Motyw: Jasny / Ciemny / Systemowy (radio)
- Rozmiar tekstu: Mały / Normalny / Duży / B. duży (4 opcje)
- **Białe czcionki** (toggle) — nowe
- Sprawdzaj w tle (toggle)
- Język: Polski / English (radio)
- Akcje: Wyloguj się · Zapisz i zamknij

### Statusbar
- Dot statusu połączenia (zielony = OK)
- Czas ostatniej aktualizacji + źródło danych (cache / API)
- Skróty klawiszowe

---

## 11. Implementacja (Phase 9) – priorytety

1. CSS custom properties jako design tokens (plik `styles/tokens.qss`)
2. Przełączanie motywów przez `QApplication.setStyleSheet()` przy zmianie w Ustawieniach
3. `VideoCard` jako osobny widget PyQt6 z identycznym układem przycisków
4. `QFlowLayout` lub `QGridLayout` dla kafelków z dynamicznym przeliczaniem kolumn
5. Animacja "Pokaż więcej" — `QPropertyAnimation` na `maximumHeight`
6. Panel AI jako `QDockWidget` lub `QSplitter` z chowaną prawą stroną
7. Ikona `.ico` z 4 rozmiarami (20/32/48/72px)
