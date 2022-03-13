from dataclasses import dataclass
from typing import Any
from flask import Request
from flask.sessions import SessionMixin

from src.Domains.Entities.WebUser import WebUser


@dataclass()
class PageContents:
    session: dict
    request: Request
    page_title: str
    login_user: WebUser
    line_user_name: str
    login_email: str
    next_page_url: str
    data: Any
    stocks: Any
    keys: Any
    labels: Any
    message: str

    def __init__(
        self,
        session: SessionMixin,
        request: Request,
        page_title: str = '',
    ):
        self.session = dict(session)
        self.login_user = session.get('login_user', None)
        self.login_email = session.get('login_email', None)
        self.next_page_url = session.get('next_page_url', '')
        self.line_user_name = ''
        self.page_title = page_title
        self.request = request
        self.data = None
        self.stocks = []
        self.keys = []
        self.labels = []
        self.message = ''
