from dataclasses import dataclass
from datetime import datetime


@dataclass()
class User:
    _id: str
    user_name: str
    line_user_name: str
    line_user_id: str
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        _id: str = None,
        name: str = 'unknown',
        line_user_name: str = 'unknown',
        line_user_id: str = None,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self._id = _id
        self.name = name
        self.line_user_name = line_user_name
        self.line_user_id = line_user_id
        self.created_at = created_at
        self.updated_at = updated_at
