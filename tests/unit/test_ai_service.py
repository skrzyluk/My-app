"""Testy OllamaChatSession - budowa payloadu i guardrail (bez realnego Ollama)."""

from unittest.mock import MagicMock, patch

import pytest

from services import ai_service as a


VIDEOS = [
    {"title": "Rust vs Go", "channel": "DevProgTV", "description": "Porownanie.",
     "duration": "18:20", "published_at": "2026-07-01", "url": "https://youtu.be/rustgo"},
    {"title": "Podstawy Pythona", "channel": "KodujZnami", "description": "Kurs.",
     "duration": "61:00", "published_at": "2026-07-05", "url": "https://youtu.be/py60"},
]


@pytest.fixture
def session():
    """Sesja z zamockowanym sprawdzeniem polaczenia (model 'dostepny')."""
    tags = MagicMock()
    tags.json.return_value = {"models": [{"name": "llama3.2:3b"}]}
    tags.raise_for_status.return_value = None
    with patch("requests.get", return_value=tags):
        return a.OllamaChatSession(list(VIDEOS), model="llama3.2:3b")


def _mock_post(reply: str):
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": reply}}
    resp.raise_for_status.return_value = None
    return resp


class TestPayload:
    def test_options_contain_gpu_and_temperature(self, session):
        with patch("requests.post", return_value=_mock_post("ok")) as post:
            session.send("czesc")
        opts = post.call_args.kwargs["json"]["options"]
        assert opts["num_gpu"] == session._num_gpu
        assert opts["temperature"] == session._temperature

    def test_default_temperature_is_low(self):
        assert a.OllamaChatSession.DEFAULT_TEMPERATURE <= 0.3

    def test_default_model_is_small(self):
        assert a.OllamaChatSession.DEFAULT_MODEL == "llama3.2:3b"

    def test_reminder_injected_in_payload(self, session):
        with patch("requests.post", return_value=_mock_post("ok")) as post:
            session.send("Co polecasz?")
        messages = post.call_args.kwargs["json"]["messages"]
        # ostatnia wiadomosc = tura usera z doklejonym przypomnieniem
        last = messages[-1]
        assert last["role"] == "user"
        assert a._TURN_REMINDER in last["content"]
        assert "Co polecasz?" in last["content"]

    def test_reminder_not_stored_in_history(self, session):
        with patch("requests.post", return_value=_mock_post("ok")):
            session.send("Co polecasz?")
        # historia: czysta tura usera (bez przypomnienia) + odpowiedz
        assert len(session._history) == 2
        assert session._history[0] == {"role": "user", "content": "Co polecasz?"}
        assert a._TURN_REMINDER not in session._history[0]["content"]

    def test_system_prompt_has_grounding_rules(self, session):
        with patch("requests.post", return_value=_mock_post("ok")) as post:
            session.send("x")
        system = post.call_args.kwargs["json"]["messages"][0]["content"]
        assert "na podstawie listy filmow" in system
        assert "wiedzy ogolnej" in system
        assert "Rust vs Go" in system  # kontekst filmow wstrzykniety

    def test_system_prompt_requires_listing_titles_on_topic_filter(self, session):
        # Regresja: pytanie "ktore filmy o X" musi wymieniac tytuly, nie sama liczbe
        with patch("requests.post", return_value=_mock_post("ok")) as post:
            session.send("x")
        system = post.call_args.kwargs["json"]["messages"][0]["content"]
        assert "filtrowanie" in system
        assert "Nie odpowiadaj sama liczba" in system


class TestErrorHandling:
    def test_reply_error_pops_user_turn(self, session):
        import requests
        with patch("requests.post", side_effect=requests.exceptions.Timeout()):
            out = session.send("cos")
        assert "czas" in out.lower() or "timeout" in out.lower()
        assert session._history == []  # tura usera cofnieta po bledzie
