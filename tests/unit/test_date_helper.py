import pytest
from datetime import timezone
from unittest.mock import patch
from utils.date_helper import get_cutoff_date, parse_iso_duration, parse_youtube_datetime


class TestGetCutoffDate:
    def test_today_returns_midnight_utc(self):
        cutoff = get_cutoff_date("today")
        assert cutoff.hour == 0
        assert cutoff.minute == 0
        assert cutoff.second == 0
        assert cutoff.tzinfo == timezone.utc

    def test_week_is_7_days_ago(self):
        from datetime import datetime, timedelta
        now = datetime.now(tz=timezone.utc)
        cutoff = get_cutoff_date("week")
        diff = now.date() - cutoff.date()
        assert diff.days == 7

    def test_month_is_30_days_ago(self):
        from datetime import datetime, timedelta
        now = datetime.now(tz=timezone.utc)
        cutoff = get_cutoff_date("month")
        diff = now.date() - cutoff.date()
        assert diff.days == 30

    def test_unknown_period_raises(self):
        with pytest.raises(ValueError, match="Unknown period"):
            get_cutoff_date("year")


class TestParseIsoDuration:
    @pytest.mark.parametrize("raw,expected", [
        ("PT45M32S",   "45:32"),
        ("PT1H5M0S",   "1:05:00"),
        ("PT30S",      "0:30"),
        ("PT0S",       "0:00"),
        ("P0D",        "0:00"),
        ("PT1H",       "1:00:00"),
        ("PT10M",      "10:00"),
        ("PT2H30M15S", "2:30:15"),
    ])
    def test_parses_correctly(self, raw, expected):
        assert parse_iso_duration(raw) == expected

    def test_empty_string_returns_question_mark(self):
        assert parse_iso_duration("") == "?"

    def test_none_returns_question_mark(self):
        assert parse_iso_duration(None) == "?"


class TestParseYoutubeDatetime:
    def test_parses_z_suffix(self):
        dt = parse_youtube_datetime("2026-06-02T14:30:00Z")
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 2
        assert dt.tzinfo is not None

    def test_parses_offset(self):
        dt = parse_youtube_datetime("2026-06-02T14:30:00+02:00")
        assert dt.tzinfo is not None
