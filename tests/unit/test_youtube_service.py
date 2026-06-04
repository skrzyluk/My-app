import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call
from googleapiclient.errors import HttpError

from services.youtube_service import (
    YouTubeService,
    YouTubeAPIError,
    QuotaExceededError,
    _chunks,
    _parse_video_item,
)


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=b"error")


def _make_service(yt_mock=None):
    return YouTubeService(yt_mock or MagicMock())


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


RECENT = _iso(datetime.now(tz=timezone.utc) - timedelta(hours=1))
OLD = _iso(datetime.now(tz=timezone.utc) - timedelta(days=60))


# ------------------------------------------------------------------ #
# _chunks                                                             #
# ------------------------------------------------------------------ #

class TestChunks:
    def test_splits_evenly(self):
        assert list(_chunks([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]

    def test_last_chunk_smaller(self):
        assert list(_chunks([1, 2, 3], 2)) == [[1, 2], [3]]

    def test_empty_list(self):
        assert list(_chunks([], 2)) == []


# ------------------------------------------------------------------ #
# _parse_video_item                                                   #
# ------------------------------------------------------------------ #

class TestParseVideoItem:
    def _item(self, **kwargs):
        base = {
            "id": "vid123",
            "snippet": {
                "channelId": "chan1",
                "title": "Test Title",
                "description": "Test desc",
                "publishedAt": RECENT,
            },
            "contentDetails": {"duration": "PT10M30S"},
        }
        base.update(kwargs)
        return base

    def test_parses_full_item(self):
        video = _parse_video_item(self._item())
        assert video.video_id == "vid123"
        assert video.title == "Test Title"
        assert video.duration == "10:30"
        assert video.url == "https://www.youtube.com/watch?v=vid123"

    def test_returns_none_on_missing_key(self):
        assert _parse_video_item({}) is None


# ------------------------------------------------------------------ #
# get_subscriptions                                                   #
# ------------------------------------------------------------------ #

class TestGetSubscriptions:
    def test_returns_channel_ids(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.return_value = {
            "items": [
                {"snippet": {"resourceId": {"channelId": "UC1"}}},
                {"snippet": {"resourceId": {"channelId": "UC2"}}},
            ]
        }
        svc = _make_service(yt)
        result = svc.get_subscriptions()
        assert result == ["UC1", "UC2"]

    def test_handles_pagination(self):
        yt = MagicMock()
        page1 = {
            "items": [{"snippet": {"resourceId": {"channelId": "UC1"}}}],
            "nextPageToken": "tok",
        }
        page2 = {
            "items": [{"snippet": {"resourceId": {"channelId": "UC2"}}}],
        }
        yt.subscriptions.return_value.list.return_value.execute.side_effect = [page1, page2]
        result = _make_service(yt).get_subscriptions()
        assert result == ["UC1", "UC2"]

    def test_returns_empty_list_when_no_subscriptions(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.return_value = {"items": []}
        assert _make_service(yt).get_subscriptions() == []


# ------------------------------------------------------------------ #
# get_upload_playlist_ids                                             #
# ------------------------------------------------------------------ #

class TestGetUploadPlaylistIds:
    def test_maps_channel_to_playlist(self):
        yt = MagicMock()
        yt.channels.return_value.list.return_value.execute.return_value = {
            "items": [
                {"id": "UC1", "contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}},
            ]
        }
        result = _make_service(yt).get_upload_playlist_ids(["UC1"])
        assert result == {"UC1": "UU1"}

    def test_batches_over_50(self):
        yt = MagicMock()
        yt.channels.return_value.list.return_value.execute.return_value = {"items": []}
        channel_ids = [f"UC{i}" for i in range(110)]
        _make_service(yt).get_upload_playlist_ids(channel_ids)
        assert yt.channels.return_value.list.call_count == 3  # 50 + 50 + 10


# ------------------------------------------------------------------ #
# get_video_ids_since                                                 #
# ------------------------------------------------------------------ #

class TestGetVideoIdsSince:
    def _playlist_item(self, video_id: str, published: str):
        return {
            "snippet": {
                "publishedAt": published,
                "resourceId": {"videoId": video_id},
            }
        }

    def test_returns_recent_videos(self):
        yt = MagicMock()
        yt.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [self._playlist_item("v1", RECENT)],
        }
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
        result = _make_service(yt).get_video_ids_since("PL1", cutoff)
        assert result == ["v1"]

    def test_stops_early_on_old_video(self):
        yt = MagicMock()
        yt.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [
                self._playlist_item("v1", RECENT),
                self._playlist_item("v2", OLD),
            ],
            "nextPageToken": "more",
        }
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
        result = _make_service(yt).get_video_ids_since("PL1", cutoff)
        assert result == ["v1"]
        assert yt.playlistItems.return_value.list.call_count == 1

    def test_skips_items_without_published_at(self):
        yt = MagicMock()
        yt.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [{"snippet": {"resourceId": {"videoId": "v1"}}}],
        }
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
        result = _make_service(yt).get_video_ids_since("PL1", cutoff)
        assert result == []


# ------------------------------------------------------------------ #
# get_video_details                                                   #
# ------------------------------------------------------------------ #

class TestGetVideoDetails:
    def _video_item(self, vid_id="v1"):
        return {
            "id": vid_id,
            "snippet": {
                "channelId": "UC1",
                "title": "Title",
                "description": "Desc",
                "publishedAt": RECENT,
            },
            "contentDetails": {"duration": "PT5M"},
        }

    def test_returns_video_objects(self):
        yt = MagicMock()
        yt.videos.return_value.list.return_value.execute.return_value = {
            "items": [self._video_item("v1"), self._video_item("v2")]
        }
        result = _make_service(yt).get_video_details(["v1", "v2"])
        assert len(result) == 2
        assert result[0].video_id == "v1"

    def test_batches_over_50(self):
        yt = MagicMock()
        yt.videos.return_value.list.return_value.execute.return_value = {"items": []}
        _make_service(yt).get_video_details([f"v{i}" for i in range(110)])
        assert yt.videos.return_value.list.call_count == 3


# ------------------------------------------------------------------ #
# Retry & error handling                                              #
# ------------------------------------------------------------------ #

class TestRetry:
    def test_retries_on_429_and_succeeds(self):
        yt = MagicMock()
        ok_response = {"items": []}
        request = MagicMock()
        request.execute.side_effect = [_http_error(429), ok_response]
        yt.subscriptions.return_value.list.return_value = request

        with patch("services.youtube_service.time.sleep") as mock_sleep:
            result = _make_service(yt).get_subscriptions()

        assert result == []
        mock_sleep.assert_called_once_with(1)

    def test_raises_quota_error_on_403(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.side_effect = _http_error(403)
        with pytest.raises(QuotaExceededError):
            _make_service(yt).get_subscriptions()

    def test_raises_after_all_retries_exhausted(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.side_effect = _http_error(503)
        with patch("services.youtube_service.time.sleep"):
            with pytest.raises(YouTubeAPIError):
                _make_service(yt).get_subscriptions()

    def test_no_retry_on_404(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.side_effect = _http_error(404)
        with pytest.raises(YouTubeAPIError):
            _make_service(yt).get_subscriptions()
        assert yt.subscriptions.return_value.list.return_value.execute.call_count == 1


# ------------------------------------------------------------------ #
# fetch_new_videos (integration of steps)                            #
# ------------------------------------------------------------------ #

class TestFetchNewVideos:
    def test_returns_empty_when_no_subscriptions(self):
        yt = MagicMock()
        yt.subscriptions.return_value.list.return_value.execute.return_value = {"items": []}
        result = _make_service(yt).fetch_new_videos("week")
        assert result == []

    def test_returns_sorted_videos(self):
        yt = MagicMock()
        older = _iso(datetime.now(tz=timezone.utc) - timedelta(hours=5))
        newer = _iso(datetime.now(tz=timezone.utc) - timedelta(hours=1))

        yt.subscriptions.return_value.list.return_value.execute.return_value = {
            "items": [{"snippet": {"resourceId": {"channelId": "UC1"}}}]
        }
        yt.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "UC1", "contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]
        }
        yt.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [
                {"snippet": {"publishedAt": older, "resourceId": {"videoId": "v_old"}}},
                {"snippet": {"publishedAt": newer, "resourceId": {"videoId": "v_new"}}},
            ]
        }
        yt.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": vid_id,
                    "snippet": {
                        "channelId": "UC1",
                        "title": f"Title {vid_id}",
                        "description": "",
                        "publishedAt": pub,
                    },
                    "contentDetails": {"duration": "PT5M"},
                }
                for vid_id, pub in [("v_old", older), ("v_new", newer)]
            ]
        }

        videos = _make_service(yt).fetch_new_videos("week")
        assert videos[0].video_id == "v_new"
        assert videos[1].video_id == "v_old"
