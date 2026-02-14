from dataclasses import dataclass
from datetime import datetime


@dataclass()
class HabitTaskLog:
    _id: str
    habit_task_id: str
    owner_id: str
    task_name_snapshot: str
    scheduled_date: str
    result: str
    note: str
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        _id: str = None,
        habit_task_id: str = None,
        owner_id: str = None,
        task_name_snapshot: str = None,
        scheduled_date: str = None,
        result: str = None,
        note: str = None,
        recorded_at: datetime = None,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self._id = _id
        self.habit_task_id = habit_task_id
        self.owner_id = owner_id
        self.task_name_snapshot = task_name_snapshot
        self.scheduled_date = scheduled_date
        self.result = result
        self.note = note
        self.recorded_at = recorded_at
        self.created_at = created_at
        self.updated_at = updated_at
