from dataclasses import dataclass
from datetime import datetime
from src.line_bot_api import line_bot_api


@dataclass()
class LineUser:
    _id: str
    line_user_name: str
    line_user_id: str
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        _id: str = None,
        line_user_name: str = None,
        line_user_id: str = None,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self._id = _id
        self.line_user_name = line_user_name
        self.line_user_id = line_user_id
        self.created_at = created_at
        self.updated_at = updated_at

    def sync_name(self):
        """_summary_
        LINEユーザ名の更新
        """
        self.line_user_name = line_bot_api.get_profile(
            self.line_user_id
        ).display_name
