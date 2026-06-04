from dataclasses import dataclass
from datetime import datetime


@dataclass
class Summary:
    period: str           # 'today' | 'week' | 'month'
    videos_count: int
    summary_text: str
    created_at: datetime
    id: int | None = None
