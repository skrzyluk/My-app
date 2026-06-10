import pytest
from datetime import datetime, timezone
from models.video import Video
from utils.summary_builder import (
    build_summary_text,
    build_single_video_text,
    _truncate,
    _format_date,
    _video_noun,
)


def _video(video_id="v1", title="Test Title", description="Desc", duration="10:30",
           published_str="2026-06-02T12:00:00Z") -> Video:
    return Video(
        video_id=video_id,
        channel_id="UC1",
        title=title,
        description=description,
        url=f"https://www.youtube.com/watch?v={video_id}",
        duration=duration,
        published_at=datetime.fromisoformat(published_str.replace("Z", "+00:00")),
    )


class TestBuildSummaryText:
    def test_header_contains_period_label(self):
        text = build_summary_text([], "week")
        assert "ostatniego tygodnia" in text

    def test_header_contains_period_label_today(self):
        text = build_summary_text([], "today")
        assert "dzisiaj" in text

    def test_header_contains_period_label_month(self):
        text = build_summary_text([], "month")
        assert "ostatniego miesiąca" in text

    def test_empty_list_shows_no_videos_message(self):
        text = build_summary_text([], "week")
        assert "Brak nowych filmów" in text

    def test_single_video_contains_title(self):
        v = _video(title="My Video")
        text = build_summary_text([v], "week")
        assert "My Video" in text

    def test_single_video_contains_link(self):
        v = _video(video_id="abc123")
        text = build_summary_text([v], "week")
        assert "https://www.youtube.com/watch?v=abc123" in text

    def test_single_video_contains_duration(self):
        v = _video(duration="45:32")
        text = build_summary_text([v], "week")
        assert "45:32" in text

    def test_multiple_videos_all_appear(self):
        videos = [_video(f"v{i}", title=f"Title {i}") for i in range(3)]
        text = build_summary_text(videos, "week")
        for i in range(3):
            assert f"Title {i}" in text

    def test_count_shown_in_header(self):
        videos = [_video(f"v{i}") for i in range(5)]
        text = build_summary_text(videos, "week")
        assert "5" in text

    def test_date_formatted_in_polish(self):
        v = _video(published_str="2026-06-02T12:00:00Z")
        text = build_summary_text([v], "week")
        assert "czerwca" in text

    def test_long_description_is_truncated(self):
        v = _video(description="A" * 200)
        text = build_summary_text([v], "week")
        assert "A" * 200 not in text
        assert "…" in text


class TestBuildSingleVideoText:
    def test_contains_title(self):
        text = build_single_video_text(_video(title="Hello"))
        assert "Hello" in text

    def test_contains_url(self):
        text = build_single_video_text(_video(video_id="xyz"))
        assert "xyz" in text

    def test_contains_duration(self):
        text = build_single_video_text(_video(duration="1:05:00"))
        assert "1:05:00" in text


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("hello", 10) == "hello"

    def test_long_string_truncated(self):
        result = _truncate("A" * 200, 120)
        assert len(result) <= 124  # 120 + ellipsis
        assert result.endswith("…")

    def test_exact_length_unchanged(self):
        assert _truncate("A" * 120, 120) == "A" * 120


class TestFormatDate:
    @pytest.mark.parametrize("iso,expected_month", [
        ("2026-01-15T12:00:00+00:00", "stycznia"),
        ("2026-03-01T12:00:00+00:00", "marca"),
        ("2026-06-04T12:00:00+00:00", "czerwca"),
        ("2026-12-31T12:00:00+00:00", "grudnia"),
    ])
    def test_polish_month_names(self, iso, expected_month):
        dt = datetime.fromisoformat(iso)
        assert expected_month in _format_date(dt)


class TestVideoNoun:
    @pytest.mark.parametrize("count,expected", [
        (0, "filmów"),
        (1, "film"),
        (2, "filmy"),
        (4, "filmy"),
        (5, "filmów"),
        (21, "filmów"),
    ])
    def test_correct_noun_form(self, count, expected):
        assert _video_noun(count) == expected
