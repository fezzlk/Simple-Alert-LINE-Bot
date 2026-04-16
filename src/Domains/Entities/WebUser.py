from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass()
class WebUser:
    _id: str
    web_user_name: str
    web_user_email: str
    linked_line_user_id: str
    is_linked_line_user: bool
    created_at: datetime
    updated_at: datetime
    encrypted_openai_api_key: Optional[str]

    def __init__(
        self,
        _id: str = None,
        web_user_name: str = None,
        web_user_email: str = None,
        linked_line_user_id: str = None,
        is_linked_line_user: bool = False,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
        encrypted_openai_api_key: Optional[str] = None,
    ):
        self._id = _id
        self.web_user_name = web_user_name
        self.web_user_email = web_user_email
        self.linked_line_user_id = linked_line_user_id
        self.is_linked_line_user = is_linked_line_user
        self.created_at = created_at
        self.updated_at = updated_at
        self.encrypted_openai_api_key = encrypted_openai_api_key
