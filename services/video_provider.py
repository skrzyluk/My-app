from google.oauth2.credentials import Credentials

from database.db import Database
from models.video import Video
from models.summary import Summary
from services.youtube_service import YouTubeService
from utils.date_helper import get_cutoff_date
from utils.summary_builder import build_summary_text
from utils.logger import get_logger

logger = get_logger(__name__)


class VideoProvider:
    """Orchestrates DB cache and YouTube API.

    The UI calls get_videos() for normal loads and force_refresh() when the
    user explicitly requests a refresh. Both paths persist results to DB and
    save a summary entry.
    """

    def __init__(self, db: Database, credentials: Credentials):
        self._db = db
        self._yt = YouTubeService.from_credentials(credentials)

    # ------------------------------------------------------------------ #
    # Public API (called from UI / background worker)                     #
    # ------------------------------------------------------------------ #

    def get_videos(self, period: str) -> list[Video]:
        """Return videos for period, using cache when fresh."""
        if self._db.is_cache_fresh():
            logger.info("Cache fresh – loading videos from DB (period=%s).", period)
            return self._videos_from_db(period)

        logger.info("Cache stale – fetching from YouTube API (period=%s).", period)
        return self._fetch_and_store(period)

    def force_refresh(self, period: str) -> list[Video]:
        """Always fetch from YouTube API, ignoring cache."""
        logger.info("Force refresh requested (period=%s).", period)
        return self._fetch_and_store(period)

    def get_new_video_count(self, period: str) -> int:
        """Return count of new videos since last saved summary (for notifications)."""
        cutoff = get_cutoff_date(period)
        return len(self._db.get_videos_since(cutoff))

    # ------------------------------------------------------------------ #
    # Internal                                                            #
    # ------------------------------------------------------------------ #

    def _fetch_and_store(self, period: str) -> list[Video]:
        videos = self._yt.fetch_new_videos(period)
        if videos:
            self._db.upsert_videos(videos)
        self._save_summary(period, videos)
        return videos

    def _videos_from_db(self, period: str) -> list[Video]:
        cutoff = get_cutoff_date(period)
        videos = self._db.get_videos_since(cutoff)
        self._save_summary(period, videos)
        return videos

    def _save_summary(self, period: str, videos: list[Video]) -> Summary:
        text = build_summary_text(videos, period)
        return self._db.save_summary(period, len(videos), text)
