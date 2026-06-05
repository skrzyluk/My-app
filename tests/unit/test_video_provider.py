import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from database.db import Database
from models.video import Video
from services.video_provider import VideoProvider


def _make_video(video_id="v1", hours_ago=1) -> Video:
    return Video(
        video_id=video_id,
        channel_id="UC1",
        title=f"Title {video_id}",
        description="",
        url=f"https://youtube.com/watch?v={video_id}",
        duration="5:00",
        published_at=datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago),
    )


@pytest.fixture
def db():
    instance = Database(db_path=":memory:")
    yield instance
    instance.close()


@pytest.fixture
def provider(db):
    mock_creds = MagicMock()
    with patch("services.video_provider.YouTubeService.from_credentials") as mock_build:
        mock_yt = MagicMock()
        mock_build.return_value = mock_yt
        p = VideoProvider(db, mock_creds)
        p._yt = mock_yt
        yield p, mock_yt, db


class TestGetVideos:
    def test_fetches_from_api_when_cache_stale(self, provider):
        prov, mock_yt, db = provider
        videos = [_make_video("v1")]
        mock_yt.fetch_new_videos.return_value = videos

        result = prov.get_videos("week")

        mock_yt.fetch_new_videos.assert_called_once_with("week")
        assert len(result) == 1
        assert result[0].video_id == "v1"

    def test_uses_db_cache_when_fresh(self, provider):
        prov, mock_yt, db = provider
        v = _make_video("v1", hours_ago=1)
        db.upsert_videos([v])

        result = prov.get_videos("week")

        mock_yt.fetch_new_videos.assert_not_called()
        assert len(result) == 1

    def test_saves_summary_on_cache_hit(self, provider):
        prov, mock_yt, db = provider
        db.upsert_videos([_make_video("v1", hours_ago=1)])

        prov.get_videos("week")

        summaries = db.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].period == "week"

    def test_saves_summary_on_api_fetch(self, provider):
        prov, mock_yt, db = provider
        mock_yt.fetch_new_videos.return_value = [_make_video("v1")]

        prov.get_videos("today")

        summaries = db.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].period == "today"

    def test_videos_upserted_to_db_after_api_fetch(self, provider):
        prov, mock_yt, db = provider
        mock_yt.fetch_new_videos.return_value = [_make_video("v1")]

        prov.get_videos("week")

        assert db.is_cache_fresh()


class TestForceRefresh:
    def test_always_calls_api_even_if_cache_fresh(self, provider):
        prov, mock_yt, db = provider
        db.upsert_videos([_make_video("v1")])
        mock_yt.fetch_new_videos.return_value = [_make_video("v2")]

        result = prov.force_refresh("week")

        mock_yt.fetch_new_videos.assert_called_once_with("week")
        assert result[0].video_id == "v2"

    def test_updates_summary_on_force_refresh(self, provider):
        prov, mock_yt, db = provider
        mock_yt.fetch_new_videos.return_value = [_make_video("v1")]
        prov.get_videos("week")

        mock_yt.fetch_new_videos.return_value = [_make_video("v1"), _make_video("v2")]
        prov.force_refresh("week")

        summaries = db.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].videos_count == 2


class TestGetNewVideoCount:
    def test_returns_correct_count(self, provider):
        prov, mock_yt, db = provider
        db.upsert_videos([_make_video("v1", hours_ago=1), _make_video("v2", hours_ago=2)])

        count = prov.get_new_video_count("week")
        assert count == 2

    def test_returns_zero_when_no_videos(self, provider):
        prov, _, db = provider
        assert prov.get_new_video_count("today") == 0
