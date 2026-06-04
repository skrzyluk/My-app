from dataclasses import dataclass
from datetime import datetime


@dataclass
class Video:
    video_id: str
    channel_id: str
    title: str
    description: str
    url: str
    duration: str        # formatted, e.g. '45:32' or '1:05:00'
    published_at: datetime

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"
