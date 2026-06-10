import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from models.video import Video
from models.summary import Summary
from utils.constants import APPDATA_DIR, CACHE_TTL_HOURS
from utils.date_helper import parse_youtube_datetime
from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_DB_PATH = APPDATA_DIR / "youtube_notifier.db"
_LAST_FETCH_KEY = "_last_fetch_at"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    video_id     TEXT PRIMARY KEY,
    channel_id   TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    url          TEXT NOT NULL,
    duration     TEXT NOT NULL DEFAULT '',
    channel_title TEXT NOT NULL DEFAULT '',
    published_at TEXT NOT NULL,
    fetched_at   TEXT NOT NULL,
    cached_until TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period       TEXT NOT NULL,
    videos_count INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_videos_published ON videos (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_cached ON videos (cached_until);
CREATE INDEX IF NOT EXISTS idx_summaries_date ON summaries (created_at DESC);
"""


class Database:
    def __init__(self, db_path: Path | str | None = None):
        path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._apply_schema()
        logger.info("Database ready at %s", path)

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------ #
    # Videos                                                              #
    # ------------------------------------------------------------------ #

    def upsert_videos(self, videos: list[Video]) -> None:
        """Insert or replace videos; sets cached_until = now + CACHE_TTL_HOURS."""
        now = _utcnow()
        cached_until = (now + timedelta(hours=CACHE_TTL_HOURS)).isoformat()
        fetched_at = now.isoformat()

        with self._conn:
            self._conn.executemany(
                """
                INSERT OR REPLACE INTO videos
                    (video_id, channel_id, title, description, url, duration,
                     channel_title, published_at, fetched_at, cached_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        v.video_id,
                        v.channel_id,
                        v.title,
                        v.description,
                        v.url,
                        v.duration,
                        v.channel_title,
                        v.published_at.isoformat(),
                        fetched_at,
                        cached_until,
                    )
                    for v in videos
                ],
            )
        logger.debug("Upserted %d videos.", len(videos))

    def get_videos_since(self, cutoff: datetime) -> list[Video]:
        """Return all cached videos published at or after cutoff, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM videos WHERE published_at >= ? ORDER BY published_at DESC",
            (cutoff.isoformat(),),
        ).fetchall()
        return [_row_to_video(r) for r in rows]

    def is_cache_fresh(self) -> bool:
        """Return True if the cache is still valid.

        The cache counts as fresh when either there is at least one video whose
        per-row TTL hasn't expired, or a successful fetch was recorded within
        CACHE_TTL_HOURS. The latter covers the case where the last fetch
        returned no new videos – without it every load would re-hit the API.
        """
        now = _utcnow()
        row = self._conn.execute(
            "SELECT 1 FROM videos WHERE cached_until > ? LIMIT 1", (now.isoformat(),)
        ).fetchone()
        if row is not None:
            return True

        last_fetch = self.get_setting(_LAST_FETCH_KEY)
        if not last_fetch:
            return False
        try:
            fetched_at = parse_youtube_datetime(last_fetch)
        except ValueError:
            return False
        return now < fetched_at + timedelta(hours=CACHE_TTL_HOURS)

    def mark_fetched(self) -> None:
        """Record the timestamp of a successful API fetch (cache validity marker)."""
        self.set_setting(_LAST_FETCH_KEY, _utcnow().isoformat())

    def clear_expired_cache(self) -> None:
        now = _utcnow().isoformat()
        with self._conn:
            self._conn.execute("DELETE FROM videos WHERE cached_until <= ?", (now,))

    # ------------------------------------------------------------------ #
    # Summaries                                                           #
    # ------------------------------------------------------------------ #

    def save_summary(self, period: str, videos_count: int, summary_text: str) -> Summary:
        """Upsert summary for today + period (one per day per period)."""
        today = _utcnow().date().isoformat()
        now = _utcnow().isoformat()

        existing = self._conn.execute(
            "SELECT id FROM summaries WHERE period = ? AND DATE(created_at) = ?",
            (period, today),
        ).fetchone()

        with self._conn:
            if existing:
                self._conn.execute(
                    """
                    UPDATE summaries
                    SET videos_count = ?, summary_text = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (videos_count, summary_text, now, existing["id"]),
                )
                row_id = existing["id"]
            else:
                cur = self._conn.execute(
                    """
                    INSERT INTO summaries (period, videos_count, summary_text, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (period, videos_count, summary_text, now),
                )
                row_id = cur.lastrowid

        return Summary(
            id=row_id,
            period=period,
            videos_count=videos_count,
            summary_text=summary_text,
            created_at=_utcnow(),
        )

    def get_summaries(self) -> list[Summary]:
        """Return all summaries, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM summaries ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_summary(r) for r in rows]

    def get_summary_by_id(self, summary_id: int) -> Summary | None:
        row = self._conn.execute(
            "SELECT * FROM summaries WHERE id = ?", (summary_id,)
        ).fetchone()
        return _row_to_summary(row) if row else None

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )

    # ------------------------------------------------------------------ #
    # Internal                                                            #
    # ------------------------------------------------------------------ #

    def _apply_schema(self) -> None:
        with self._conn:
            self._conn.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        """Apply lightweight, idempotent migrations to pre-existing databases."""
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(videos)")}
        if "channel_title" not in cols:
            with self._conn:
                self._conn.execute(
                    "ALTER TABLE videos ADD COLUMN channel_title TEXT NOT NULL DEFAULT ''"
                )
            logger.info("Migrated videos table: added channel_title column.")


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _row_to_video(row: sqlite3.Row) -> Video:
    return Video(
        video_id=row["video_id"],
        channel_id=row["channel_id"],
        title=row["title"],
        description=row["description"],
        url=row["url"],
        duration=row["duration"],
        published_at=parse_youtube_datetime(row["published_at"]),
        channel_title=row["channel_title"] if "channel_title" in row.keys() else "",
    )


def _row_to_summary(row: sqlite3.Row) -> Summary:
    return Summary(
        id=row["id"],
        period=row["period"],
        videos_count=row["videos_count"],
        summary_text=row["summary_text"],
        created_at=parse_youtube_datetime(row["created_at"]),
    )
