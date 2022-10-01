from dataclasses import dataclass
from datetime import datetime


@dataclass()
class UserSetting:
    _id: str
    web_user_id: str
    is_notify_when_nothing_near_expiry: bool
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        _id: str = None,
        web_user_id: str = None,
        is_notify_when_nothing_near_expiry: bool = True,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self._id = _id
        self.web_user_id = web_user_id
        self.is_notify_when_nothing_near_expiry = is_notify_when_nothing_near_expiry
        self.created_at = created_at
        self.updated_at = updated_at
