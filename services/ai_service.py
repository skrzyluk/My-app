"""AI service - Ollama integration for YouTube Notifier.

Uzywa lokalnego modelu przez Ollama (POST /api/chat).
URL i model konfigurowane w Ustawieniach aplikacji.

Uzycie:
    session = create_chat_session(videos)
    reply   = session.send("Podsumuj filmy")
"""

from __future__ import annotations

import logging
from typing import Optional

import keyring

logger = logging.getLogger(__name__)

_KEYRING_SERVICE = "YouTubeNotifier"
_KEYRING_KEY     = "gemini_api_key"


def get_api_key() -> Optional[str]:
    try:
        return keyring.get_password(_KEYRING_SERVICE, _KEYRING_KEY)
    except Exception:
        return None


def save_api_key(key: str) -> None:
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_KEY, key.strip())


def delete_api_key() -> None:
    try:
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_KEY)
    except Exception:
        pass


def api_key_is_set() -> bool:
    key = get_api_key()
    return bool(key and key.strip())


# ------------------------------------------------------------
# Video context builder
# ------------------------------------------------------------

def build_video_context(videos: list) -> str:
    if not videos:
        return "Brak filmow."
    lines = []
    for i, v in enumerate(videos, 1):
        if hasattr(v, "title"):
            title    = v.title
            channel  = getattr(v, "channel_title", getattr(v, "channel_id", "nieznany"))
            desc     = (v.description or "")[:300]
            duration = v.duration
            date     = str(v.published_at)[:10]
            url      = v.url
        else:
            title    = v.get("title", "")
            channel  = v.get("channel", "")
            desc     = v.get("description", "")[:300]
            duration = v.get("duration", "")
            date     = v.get("published_at", "")
            url      = v.get("url", "")
        lines.append(
            f"{i}. Tytul: {title}\n"
            f"   Kanal: {channel}\n"
            f"   Dlugosc: {duration} | Data: {date}\n"
            f"   Opis: {desc}\n"
            f"   Link: {url}"
        )
    return "\n\n".join(lines)


_SYSTEM_PROMPT = (
    "Jestes asystentem aplikacji YouTube Notifier. Twoim jedynym zadaniem jest "
    "pomagac uzytkownikowi analizowac liste filmow podana ponizej.\n\n"
    "ZASADY:\n"
    "- Odpowiadaj wylacznie w oparciu o informacje z listy filmow.\n"
    "- Jesli pytanie nie dotyczy filmow z listy, grzecznie odmow.\n"
    "- Odpowiadaj po polsku, chyba ze uzytkownik pisze po angielsku.\n"
    "- Badz zwiezly i konkretny.\n"
    "- Mozesz polecac filmy, porownywac je, streszczac opisy i odpowiadac na "
    "pytania o ich tematyke."
)


def build_system_prompt(videos: list) -> str:
    context = build_video_context(videos)
    n = len(videos)
    return (
        f"{_SYSTEM_PROMPT}\n\n"
        f"LISTA FILMOW ({n} filmow):\n---\n{context}\n---"
    )


# ------------------------------------------------------------
# OllamaChatSession
# ------------------------------------------------------------

class OllamaChatSession:
    """Stateful Ollama chat session grounded in the current video list.

    Korzysta z natywnego API Ollama (POST /api/chat, stream=false).
    Wymagania: Ollama uruchomione lokalnie, pobrany wybrany model.
    """

    DEFAULT_URL   = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"

    def __init__(self, videos: list, url: str = DEFAULT_URL, model: str = DEFAULT_MODEL):
        self._videos  = videos
        self._url     = url.rstrip("/")
        self._model   = model
        self._history: list[dict] = []
        self._system_prompt = build_system_prompt(videos)
        self._check_connection()
        logger.info(
            "OllamaChatSession initialized (model=%s, url=%s, videos=%d)",
            self._model, self._url, len(self._videos),
        )

    def _check_connection(self) -> None:
        import requests
        try:
            r = requests.get(f"{self._url}/api/tags", timeout=5)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Nie mozna polaczyc sie z Ollama pod adresem {self._url}.\n"
                "Upewnij sie, ze Ollama jest uruchomione."
            )
        except Exception as exc:
            raise RuntimeError(f"Blad polaczenia z Ollama: {exc}")
        available = [m["name"] for m in data.get("models", [])]
        base_model = self._model.split(":")[0]
        found = any(m.split(":")[0] == base_model for m in available)
        if not found:
            models_str = ", ".join(available) if available else "(brak pobranych)"
            raise RuntimeError(
                f"Model {self._model!r} nie jest pobrany w Ollama.\n"
                f"Dostepne modele: {models_str}\n"
                f"Pobierz: ollama pull {self._model}"
            )

    def send(self, user_message: str) -> str:
        import requests
        self._history.append({"role": "user", "content": user_message})
        payload = {
            "model":    self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                *self._history,
            ],
            "stream": False,
        }
        try:
            r = requests.post(f"{self._url}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            reply = r.json()["message"]["content"]
            self._history.append({"role": "assistant", "content": reply})
            logger.debug("Ollama reply (%d chars)", len(reply))
            return reply
        except requests.exceptions.ConnectionError:
            self._history.pop()
            return "Utracono polaczenie z Ollama. Upewnij sie, ze Ollama nadal dziala."
        except requests.exceptions.Timeout:
            self._history.pop()
            return "Przekroczono czas odpowiedzi modelu (120 s). Sprobuj ponownie."
        except Exception as exc:
            self._history.pop()
            logger.exception("Ollama API error")
            return f"Blad Ollama: {str(exc)[:200]}"

    def reset(self, videos: list | None = None) -> None:
        if videos is not None:
            self._videos = videos
            self._system_prompt = build_system_prompt(videos)
        self._history = []


# Alias dla kompatybilnosci wstecznej
ChatSession = OllamaChatSession


# ------------------------------------------------------------
# Factory
# ------------------------------------------------------------

def create_chat_session(videos: list) -> OllamaChatSession:
    """Utworz sesje czatu Ollama. URL i model czyta z AppSettings."""
    try:
        from config.settings import AppSettings
        s = AppSettings()
        url   = s.ollama_url()
        model = s.ollama_model()
    except Exception:
        url   = OllamaChatSession.DEFAULT_URL
        model = OllamaChatSession.DEFAULT_MODEL
    return OllamaChatSession(videos, url=url, model=model)
