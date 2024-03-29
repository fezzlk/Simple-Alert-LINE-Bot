from dataclasses import dataclass
from typing import Any, List, Generic, TypeVar, Optional
from flask import Request
from flask.sessions import SessionMixin

from src.Domains.Entities.WebUser import WebUser
from src.models.StockViewModel import StockViewModel


@dataclass()
class RegisterFormData:
    login_name: str
    login_email: str

    def __init__(
        self,
        session: SessionMixin,
    ):
        self.login_name = session['login_name']
        self.login_email = session['login_email']

@dataclass()
class StockListData:
    stocks: List[StockViewModel]
    keys: List[str]
    labels: List[str]

    def __init__(
        self,
        session: SessionMixin,
    ):
        self.stocks = []
        self.keys = []
        self.labels = []

T = TypeVar('T', RegisterFormData, StockListData, None)

@dataclass()
class PageContents(Generic[T]):
    session: dict
    request: Request
    page_title: str
    login_user: WebUser
    line_user_name: str
    next_page_url: str
    data: T
    message: str

    def __init__(
        self,
        session: SessionMixin,
        request: Request,
        DataClass: T = None,
        page_title: str = '',
    ):
        self.session = dict(session)
        self.login_user = session.get('login_user', None)
        self.next_page_url = session.get('next_page_url', '')
        self.line_user_name = ''
        self.page_title = page_title
        self.request = request
        self.message = ''
        if DataClass is not None:
            self.data = DataClass(session)
