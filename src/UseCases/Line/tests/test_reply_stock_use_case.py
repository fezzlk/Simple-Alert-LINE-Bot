from datetime import datetime

from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.ReplyStockUseCase import ReplyStockUseCase


class DummyLineRequestService(ILineRequestService):
    def __init__(self, user_id: str):
        self._message = ""
        self._event_type = "message"
        self._req_line_user_name = "dummy"
        self._req_line_user_id = user_id
        self._req_line_group_id = None

    @property
    def message(self) -> str:
        return self._message

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def req_line_user_name(self) -> str:
        return self._req_line_user_name

    @property
    def req_line_user_id(self) -> str:
        return self._req_line_user_id

    @property
    def req_line_group_id(self) -> str:
        return self._req_line_group_id

    def set_req_info(self, event) -> None:
        pass

    def delete_req_info(self) -> None:
        pass


class DummyLineResponseService(ILineResponseService):
    def __init__(self):
        self.messages = []

    def add_message(self, text: str) -> None:
        self.messages.append(text)

    def add_image(self, image_url: str) -> None:
        pass

    def reply(self, event) -> None:
        pass

    def push(self, to: str) -> None:
        pass

    def reset(self) -> None:
        pass

    def push_a_message(self, to: str, message: str) -> None:
        pass


class DummyWebUserRepository(IWebUserRepository):
    def __init__(self, web_users: list[WebUser]):
        self._web_users = web_users

    def create(self, new_web_user: WebUser) -> WebUser:
        return new_web_user

    def update(self, query, new_web_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list[WebUser]:
        return self._web_users


class DummyStockRepository(IStockRepository):
    def __init__(self, stocks: list[Stock]):
        self._stocks = stocks

    def create(self, new_stock: Stock) -> Stock:
        return new_stock

    def update(self, query, new_stock) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list[Stock]:
        return self._stocks


def test_reply_stock_with_and_without_expiry_dates(monkeypatch):
    fixed_now = datetime(2025, 1, 10, 0, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(
        "src.UseCases.Line.ReplyStockUseCase.datetime",
        FixedDatetime,
    )

    stocks = [
        Stock(item_name="no_expiry", owner_id="U1", expiry_date=None, status=1, created_at=fixed_now),
        Stock(item_name="with_expiry", owner_id="U1", expiry_date=datetime(2025, 1, 20), status=1, created_at=fixed_now),
    ]
    web_user = WebUser(
        _id="W1",
        web_user_name="dummy",
        web_user_email="dummy@example.com",
        linked_line_user_id="U1",
        is_linked_line_user=True,
    )

    use_case = ReplyStockUseCase(
        stock_repository=DummyStockRepository(stocks),
        web_user_repository=DummyWebUserRepository([web_user]),
        line_request_service=DummyLineRequestService(user_id="U1"),
        line_response_service=DummyLineResponseService(),
    )

    use_case.execute()

    messages = use_case._line_response_service.messages
    joined = "\n".join(messages)
    assert "no_expiry" in joined
    assert "with_expiry" in joined
