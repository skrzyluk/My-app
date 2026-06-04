import re
from datetime import datetime, timezone, timedelta


def get_cutoff_date(period: str) -> datetime:
    """Return the start datetime (UTC, timezone-aware) for the given period.

    Args:
        period: 'today' | 'week' | 'month'
    """
    now = datetime.now(tz=timezone.utc)
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown period: {period!r}. Expected 'today', 'week' or 'month'.")


def parse_iso_duration(duration: str) -> str:
    """Convert ISO 8601 duration to a human-readable string.

    Examples:
        PT45M32S  → '45:32'
        PT1H5M    → '1:05:00'
        PT30S     → '0:30'
        P0D       → '0:00'
    """
    match = re.fullmatch(
        r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration or "",
    )
    if not match:
        return duration or "?"

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0) + days * 24
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def parse_youtube_datetime(dt_str: str) -> datetime:
    """Parse a YouTube API datetime string to a timezone-aware datetime."""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
