from typing import Optional
from flask.sessions import SessionMixin

from src.Domains.Entities.WebUser import WebUser


def build_login_user(session: SessionMixin) -> Optional[WebUser]:
    login_user = session.get('login_user', None)
    if isinstance(login_user, dict):
        return WebUser(
            _id=login_user.get("_id"),
            web_user_name=login_user.get("web_user_name"),
            web_user_email=login_user.get("web_user_email"),
            linked_line_user_id=login_user.get("linked_line_user_id"),
            is_linked_line_user=bool(login_user.get("is_linked_line_user")),
        )
    if isinstance(login_user, WebUser):
        return login_user
    return None
