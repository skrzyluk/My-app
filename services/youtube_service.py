import time
from datetime import datetime
from typing import Generator

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from models.video import Video
from utils.constants import (
    MAX_RESULTS,
    RETRY_DELAYS,
    YOUTUBE_API_SERVICE,
    YOUTUBE_API_VERSION,
)
from utils.date_helper import get_cutoff_date, parse_iso_duration, parse_youtube_datetime
from utils.logger import get_logger

logger = get_logger(__name__)

_RETRYABLE_STATUS = {429, 500, 503}
_BATCH_SIZE = 50


class YouTubeAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class QuotaExceededError(YouTubeAPIError):
    pass


class YouTubeService:
    def __init__(self, youtube_resource):
        self._yt = youtube_resource

    @classmethod
    def from_credentials(cls, credentials: Credentials) -> "YouTubeService":
        resource = build(
            YOUTUBE_API_SERVICE,
            YOUTUBE_API_VERSION,
            credentials=credentials,
            cache_discovery=False,
        )
        return cls(resource)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def fetch_new_videos(self, period: str) -> list[Video]:
        """Return all new videos from subscribed channels for the given period.

        Args:
            period: 'today' | 'week' | 'month'
        """
        cutoff = get_cutoff_date(period)
        logger.info("Fetching videos since %s (period=%s)", cutoff.isoformat(), period)

        channel_ids = self.get_subscriptions()
        if not channel_ids:
            logger.info("No subscriptions found.")
            return []

        playlist_map = self.get_upload_playlist_ids(channel_ids)

        video_ids: list[str] = []
        for playlist_id in playlist_map.values():
            ids = self.get_video_ids_since(playlist_id, cutoff)
            video_ids.extend(ids)

        if not video_ids:
            return []

        videos = self.get_video_details(video_ids)
        videos.sort(key=lambda v: v.published_at, reverse=True)
        return videos

    def get_subscriptions(self) -> list[str]:
        """Return channel IDs of all subscribed channels (paginated)."""
        channel_ids: list[str] = []
        page_token = None

        while True:
            resp = self._execute(
                self._yt.subscriptions().list(
                    mine=True,
                    part="snippet",
                    maxResults=MAX_RESULTS,
                    pageToken=page_token,
                )
            )
            for item in resp.get("items", []):
                cid = item["snippet"]["resourceId"]["channelId"]
                channel_ids.append(cid)

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info("Found %d subscriptions.", len(channel_ids))
        return channel_ids

    def get_upload_playlist_ids(self, channel_ids: list[str]) -> dict[str, str]:
        """Return {channelId: uploadsPlaylistId} for the given channel IDs."""
        result: dict[str, str] = {}

        for chunk in _chunks(channel_ids, _BATCH_SIZE):
            resp = self._execute(
                self._yt.channels().list(
                    part="contentDetails",
                    id=",".join(chunk),
                    maxResults=_BATCH_SIZE,
                )
            )
            for item in resp.get("items", []):
                cid = item["id"]
                playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
                result[cid] = playlist_id

        return result

    def get_video_ids_since(self, playlist_id: str, cutoff: datetime) -> list[str]:
        """Return video IDs from a playlist published at or after cutoff."""
        video_ids: list[str] = []
        page_token = None

        while True:
            resp = self._execute(
                self._yt.playlistItems().list(
                    playlistId=playlist_id,
                    part="snippet",
                    maxResults=MAX_RESULTS,
                    pageToken=page_token,
                )
            )

            stop = False
            for item in resp.get("items", []):
                published_str = item["snippet"].get("publishedAt")
                if not published_str:
                    continue
                published = parse_youtube_datetime(published_str)
                if published < cutoff:
                    stop = True
                    break
                vid = item["snippet"]["resourceId"]["videoId"]
                video_ids.append(vid)

            page_token = resp.get("nextPageToken")
            if stop or not page_token:
                break

        return video_ids

    def get_video_details(self, video_ids: list[str]) -> list[Video]:
        """Fetch full video details for the given IDs (batched)."""
        videos: list[Video] = []

        for chunk in _chunks(video_ids, _BATCH_SIZE):
            resp = self._execute(
                self._yt.videos().list(
                    part="snippet,contentDetails",
                    id=",".join(chunk),
                    maxResults=_BATCH_SIZE,
                )
            )
            for item in resp.get("items", []):
                video = _parse_video_item(item)
                if video:
                    videos.append(video)

        return videos

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _execute(self, request):
        last_error: Exception | None = None

        for attempt, delay in enumerate([0] + list(RETRY_DELAYS)):
            if delay:
                time.sleep(delay)
            try:
                return request.execute()
            except HttpError as e:
                status = int(e.resp.status)
                if status == 403:
                    raise QuotaExceededError(
                        f"YouTube API quota exceeded (403): {e}", status_code=403
                    ) from e
                if status not in _RETRYABLE_STATUS:
                    raise YouTubeAPIError(str(e), status_code=status) from e
                last_error = e
                logger.warning(
                    "API error %s on attempt %d/%d, retrying…",
                    status, attempt + 1, len(RETRY_DELAYS) + 1,
                )

        raise YouTubeAPIError(str(last_error)) from last_error


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #

def _chunks(lst: list, n: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def _parse_video_item(item: dict) -> Video | None:
    try:
        snippet = item["snippet"]
        details = item["contentDetails"]
        video_id = item["id"]
        return Video(
            video_id=video_id,
            channel_id=snippet.get("channelId", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            url=f"https://www.youtube.com/watch?v={video_id}",
            duration=parse_iso_duration(details.get("duration", "")),
            published_at=parse_youtube_datetime(snippet["publishedAt"]),
        )
    except (KeyError, ValueError) as e:
        logger.warning("Failed to parse video item: %s", e)
        return None
