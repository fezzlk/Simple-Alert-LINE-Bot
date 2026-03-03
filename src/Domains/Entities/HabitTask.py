from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass()
class HabitTask:
    _id: str
    owner_id: str
    task_name: str
    frequency: str
    notify_time: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    notify_day_of_week: Optional[int]   # 0=月〜6=日（weekly用）
    notify_day_of_month: Optional[int]  # 1〜31（monthly用）

    def __init__(
        self,
        _id: str = None,
        owner_id: str = None,
        task_name: str = None,
        frequency: str = "daily",
        notify_time: str = "12:00",
        is_active: bool = True,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
        notify_day_of_week: Optional[int] = None,
        notify_day_of_month: Optional[int] = None,
        **kwargs,
    ):
        self._id = _id
        self.owner_id = owner_id
        self.task_name = task_name
        self.frequency = frequency
        self.notify_time = notify_time
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.notify_day_of_week = notify_day_of_week
        self.notify_day_of_month = notify_day_of_month
