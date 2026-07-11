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


# Ujednolicona formula odmowy dla pytan spoza listy
REFUSAL_PL = "Moge rozmawiac wylacznie o filmach z Twojej listy."

_SYSTEM_PROMPT = (
    "Jestes asystentem aplikacji YouTube Notifier. Pomagasz uzytkownikowi "
    "zorientowac sie w jego liscie pobranych filmow z YouTube (ponizej).\n\n"
    "ZASADY:\n"
    "- Odpowiadaj wylacznie na podstawie listy filmow ponizej. Nie dodawaj wiedzy "
    "ogolnej spoza listy i nie wymyslaj filmow. Uzywaj tytulow i linkow doslownie "
    "z listy.\n"
    "- Gdy user pyta 'ktore/jakie filmy sa o <temat>' albo prosi o filtrowanie "
    "listy, przejrzyj cala liste i wymien pasujace filmy po tytule wraz z linkiem. "
    "Nie odpowiadaj sama liczba (np. 'dwa filmy') - zawsze wypisz ktore to sa. "
    "Jesli zaden nie pasuje, napisz: 'Zaden film z listy nie dotyczy tego tematu'.\n"
    "- Mozesz polecac filmy, porownywac je, streszczac opisy, sortowac po dlugosci "
    "lub dacie. Kontynuacje typu 'podaj link', 'a drugi?', 'stresc go' obsluguj "
    "normalnie.\n"
    "- Jesli user prosi o cos zupelnie niezwiazanego z filmami (rozwiazanie "
    "zadania matematycznego, napisanie kodu lub wiersza, zart, wyjasnienie "
    f"ogolnego tematu), odpowiedz krotko: \"{REFUSAL_PL}\"\n"
    "- Odpowiadaj po polsku (lub angielsku, jesli user pisze po angielsku), "
    "zwiezle, ale zawsze konkretnie wymieniaj filmy, gdy o nie chodzi."
)

# Krotkie przypomnienie wstrzykiwane przy KAZDEJ turze (male modele lepiej
# trzymaja sie regul, gdy sa one blisko biezacego pytania).
_TURN_REMINDER = (
    "Pamietaj: korzystaj tylko z listy filmow powyzej. Gdy pytanie dotyczy tematu "
    "('ktore filmy o X'), przejrzyj liste i wymien pasujace tytuly z linkami."
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
    DEFAULT_MODEL = "llama3.2:3b"

    DEFAULT_NUM_GPU = 999  # 999 = pelny offload na GPU (Nvidia). Jednolity backend
                           # unika crasha llama-server przy czesciowym offloadzie
                           # (GGML_SCHED_MAX_SPLIT_INPUTS). 0 = wszystko na CPU.

    DEFAULT_TEMPERATURE = 0.1  # Niska temp = model trzyma sie listy filmow i nie
                               # halucynuje tytulow spoza kontekstu.

    def __init__(self, videos: list, url: str = DEFAULT_URL, model: str = DEFAULT_MODEL,
                 num_gpu: int = DEFAULT_NUM_GPU, temperature: float = DEFAULT_TEMPERATURE):
        self._videos  = videos
        self._url     = url.rstrip("/")
        self._model   = model
        self._num_gpu = num_gpu
        self._temperature = temperature
        self._history: list[dict] = []
        self._system_prompt = build_system_prompt(videos)
        self._check_connection()
        logger.info(
            "OllamaChatSession initialized (model=%s, url=%s, num_gpu=%s, temp=%s, videos=%d)",
            self._model, self._url, self._num_gpu, self._temperature, len(self._videos),
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
        # Efemeryczna kopia biezacej tury z doklejonym przypomnieniem regul
        # (nie zapisujemy go w historii, by nie zasmiecac kontekstu).
        ephemeral_user = {
            "role": "user",
            "content": f"{user_message}\n\n[{_TURN_REMINDER}]",
        }
        payload = {
            "model":    self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                *self._history[:-1],
                ephemeral_user,
            ],
            "stream": False,
            "options": {
                "num_gpu":     self._num_gpu,
                "temperature": self._temperature,
            },
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
        url     = s.ollama_url()
        model   = s.ollama_model()
        num_gpu = s.ollama_num_gpu()
        temp    = s.ollama_temperature()
    except Exception:
        url     = OllamaChatSession.DEFAULT_URL
        model   = OllamaChatSession.DEFAULT_MODEL
        num_gpu = OllamaChatSession.DEFAULT_NUM_GPU
        temp    = OllamaChatSession.DEFAULT_TEMPERATURE
    return OllamaChatSession(videos, url=url, model=model, num_gpu=num_gpu, temperature=temp)
