from dataclasses import dataclass
from datetime import datetime


@dataclass()
class NotificationSchedule:
    line_user_id: str
    notify_time: str
    timezone: str
    enabled: bool
    next_notify_at: datetime
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        line_user_id: str = None,
        notify_time: str = "12:00",
        timezone: str = "Asia/Tokyo",
        enabled: bool = True,
        next_notify_at: datetime = None,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self.line_user_id = line_user_id
        self.notify_time = notify_time
        self.timezone = timezone
        self.enabled = enabled
        self.next_notify_at = next_notify_at
        self.created_at = created_at
        self.updated_at = updated_at
