from datetime import datetime
from models.video import Video

_PERIOD_LABELS = {
    "today":  "dzisiaj",
    "week":   "ostatniego tygodnia",
    "month":  "ostatniego miesiąca",
}


def build_summary_text(videos: list[Video], period: str) -> str:
    """Build a human-readable summary string from a list of videos."""
    label = _PERIOD_LABELS.get(period, period)
    count = len(videos)
    noun = _video_noun(count)

    header = f"📺 Nowe filmy z {label} ({count} {noun}):"

    if not videos:
        return header + "\n\nBrak nowych filmów."

    lines = [header, ""]
    for v in videos:
        lines += [
            f'• Tytuł: "{v.title}"',
            f'  Opis: "{_truncate(v.description, 120)}"',
            f"  Link: {v.url}",
            f"  Długość: {v.duration}",
            f"  Data publikacji: {_format_date(v.published_at)}",
            "",
        ]

    return "\n".join(lines).rstrip()


def build_single_video_text(video: Video) -> str:
    """Build a clipboard-ready string for a single video."""
    return (
        f'Tytuł: "{video.title}"\n'
        f'Opis: "{_truncate(video.description, 120)}"\n'
        f"Link: {video.url}\n"
        f"Długość: {video.duration}\n"
        f"Data publikacji: {_format_date(video.published_at)}"
    )


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def _format_date(dt: datetime) -> str:
    months = [
        "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
    ]
    d = dt.astimezone()
    return f"{d.day} {months[d.month - 1]} {d.year}"


def _video_noun(count: int) -> str:
    if count == 1:
        return "film"
    if 2 <= count <= 4:
        return "filmy"
    return "filmów"
