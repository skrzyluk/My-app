import pytest
from datetime import datetime, timezone, timedelta

from database.db import Database
from models.video import Video
from models.summary import Summary


@pytest.fixture
def db():
    """In-memory database, fresh for each test."""
    instance = Database(db_path=":memory:")
    yield instance
    instance.close()


def _make_video(video_id="v1", channel_id="UC1", hours_ago=1) -> Video:
    published = datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)
    return Video(
        video_id=video_id,
        channel_id=channel_id,
        title=f"Title {video_id}",
        description="Desc",
        url=f"https://youtube.com/watch?v={video_id}",
        duration="10:00",
        published_at=published,
    )


# ------------------------------------------------------------------ #
# upsert_videos / get_videos_since                                    #
# ------------------------------------------------------------------ #

class TestUpsertAndGetVideos:
    def test_insert_and_retrieve(self, db):
        v = _make_video("v1", hours_ago=1)
        db.upsert_videos([v])
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=2)
        results = db.get_videos_since(cutoff)
        assert len(results) == 1
        assert results[0].video_id == "v1"
        assert results[0].title == "Title v1"

    def test_returns_empty_when_no_videos_after_cutoff(self, db):
        v = _make_video("v1", hours_ago=48)
        db.upsert_videos([v])
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        assert db.get_videos_since(cutoff) == []

    def test_replace_on_duplicate_id(self, db):
        v1 = _make_video("v1")
        db.upsert_videos([v1])
        v1_updated = Video(
            video_id="v1",
            channel_id="UC1",
            title="Updated Title",
            description="",
            url="https://youtube.com/watch?v=v1",
            duration="5:00",
            published_at=v1.published_at,
        )
        db.upsert_videos([v1_updated])
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=2)
        results = db.get_videos_since(cutoff)
        assert len(results) == 1
        assert results[0].title == "Updated Title"

    def test_sorted_newest_first(self, db):
        v_old = _make_video("v_old", hours_ago=5)
        v_new = _make_video("v_new", hours_ago=1)
        db.upsert_videos([v_old, v_new])
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=10)
        results = db.get_videos_since(cutoff)
        assert results[0].video_id == "v_new"
        assert results[1].video_id == "v_old"

    def test_multiple_videos(self, db):
        videos = [_make_video(f"v{i}", hours_ago=i) for i in range(1, 6)]
        db.upsert_videos(videos)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=10)
        assert len(db.get_videos_since(cutoff)) == 5


# ------------------------------------------------------------------ #
# is_cache_fresh / clear_expired_cache                               #
# ------------------------------------------------------------------ #

class TestCacheValidity:
    def test_fresh_after_insert(self, db):
        db.upsert_videos([_make_video()])
        assert db.is_cache_fresh() is True

    def test_not_fresh_on_empty_db(self, db):
        assert db.is_cache_fresh() is False

    def test_clear_expired_removes_old_entries(self, db):
        import sqlite3
        from utils.constants import APPDATA_DIR

        v = _make_video("v1")
        db.upsert_videos([v])

        # Manually expire the cache
        past = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
        db._conn.execute("UPDATE videos SET cached_until = ?", (past,))
        db._conn.commit()

        db.clear_expired_cache()
        assert db.is_cache_fresh() is False


# ------------------------------------------------------------------ #
# save_summary / get_summaries                                        #
# ------------------------------------------------------------------ #

class TestSummaries:
    def test_save_and_retrieve(self, db):
        s = db.save_summary("week", 3, "Summary text")
        assert s.id is not None
        summaries = db.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].period == "week"
        assert summaries[0].videos_count == 3

    def test_deduplication_same_day_same_period(self, db):
        db.save_summary("week", 3, "First")
        db.save_summary("week", 5, "Updated")
        summaries = db.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].videos_count == 5
        assert summaries[0].summary_text == "Updated"

    def test_no_dedup_different_period(self, db):
        db.save_summary("today", 1, "Today")
        db.save_summary("week", 3, "Week")
        assert len(db.get_summaries()) == 2

    def test_summaries_sorted_newest_first(self, db):
        db.save_summary("today", 1, "Today")
        db.save_summary("week", 3, "Week")
        summaries = db.get_summaries()
        # Both created today; second insert should appear first
        assert summaries[0].period == "week"

    def test_get_summary_by_id(self, db):
        s = db.save_summary("month", 10, "Month")
        fetched = db.get_summary_by_id(s.id)
        assert fetched is not None
        assert fetched.period == "month"

    def test_get_summary_by_id_returns_none_for_missing(self, db):
        assert db.get_summary_by_id(999) is None


# ------------------------------------------------------------------ #
# Settings                                                            #
# ------------------------------------------------------------------ #

class TestSettings:
    def test_set_and_get(self, db):
        db.set_setting("language", "pl")
        assert db.get_setting("language") == "pl"

    def test_get_returns_default_when_missing(self, db):
        assert db.get_setting("missing_key", "default_val") == "default_val"

    def test_get_returns_none_when_no_default(self, db):
        assert db.get_setting("missing_key") is None

    def test_update_existing_setting(self, db):
        db.set_setting("theme", "dark")
        db.set_setting("theme", "light")
        assert db.get_setting("theme") == "light"

    def test_multiple_settings_independent(self, db):
        db.set_setting("language", "pl")
        db.set_setting("theme", "dark")
        assert db.get_setting("language") == "pl"
        assert db.get_setting("theme") == "dark"


# ------------------------------------------------------------------ #
# watched state                                                       #
# ------------------------------------------------------------------ #

class TestWatchedState:
    def _get(self, db, video_id="v1"):
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=48)
        return next(v for v in db.get_videos_since(cutoff) if v.video_id == video_id)

    def test_default_not_watched(self, db):
        db.upsert_videos([_make_video("v1")])
        assert self._get(db).watched is False

    def test_set_watched_true(self, db):
        db.upsert_videos([_make_video("v1")])
        db.set_watched("v1", True)
        assert self._get(db).watched is True

    def test_set_watched_toggle_back(self, db):
        db.upsert_videos([_make_video("v1")])
        db.set_watched("v1", True)
        db.set_watched("v1", False)
        assert self._get(db).watched is False

    def test_watched_survives_reupsert(self, db):
        # Re-fetching the same video must NOT reset its watched flag.
        v = _make_video("v1")
        db.upsert_videos([v])
        db.set_watched("v1", True)
        db.upsert_videos([v])  # simulate a refresh
        assert self._get(db).watched is True
