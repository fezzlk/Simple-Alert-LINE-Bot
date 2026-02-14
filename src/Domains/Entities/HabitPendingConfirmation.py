from dataclasses import dataclass
from datetime import datetime


@dataclass()
class HabitPendingConfirmation:
    _id: str
    line_user_id: str
    habit_task_id: str
    owner_id: str
    scheduled_date: str
    status: str
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        _id: str = None,
        line_user_id: str = None,
        habit_task_id: str = None,
        owner_id: str = None,
        scheduled_date: str = None,
        status: str = "awaiting_answer",
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self._id = _id
        self.line_user_id = line_user_id
        self.habit_task_id = habit_task_id
        self.owner_id = owner_id
        self.scheduled_date = scheduled_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
