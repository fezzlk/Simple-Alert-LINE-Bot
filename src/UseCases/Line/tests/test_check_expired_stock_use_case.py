from datetime import datetime

from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase


class DummyLineUserRepository(ILineUserRepository):
    def __init__(self, line_users: list[LineUser], web_users: list[WebUser]):
        self._line_users = line_users
        self._web_users = web_users

    def create(self, new_line_user: LineUser) -> LineUser:
        return new_line_user

    def update(self, query, new_line_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query: dict = None) -> list[LineUser]:
        if not query:
            return self._line_users
        if "linked_line_user_id" in str(query):
            return self._web_users
        return []


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


class DummyLineResponseService(ILineResponseService):
    def __init__(self):
        self.messages = []
        self.pushes = []

    def add_message(self, text: str) -> None:
        self.messages.append(text)

    def add_image(self, image_url: str) -> None:
        pass

    def reply(self, event) -> None:
        pass

    def push(self, to: str) -> None:
        self.pushes.append(to)

    def reset(self) -> None:
        pass

    def push_a_message(self, to: str, message: str) -> None:
        pass


def test_check_expired_stock_sends_expected_messages(monkeypatch):
    fixed_now = datetime(2025, 1, 10, 0, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(
        "src.UseCases.Line.CheckExpiredStockUseCase.datetime",
        FixedDatetime,
    )

    line_user = LineUser(
        line_user_name="dummy",
        line_user_id="U1",
    )
    web_user = WebUser(
        _id="W1",
        web_user_name="web",
        web_user_email="web@example.com",
        linked_line_user_id="U1",
        is_linked_line_user=True,
    )

    stocks = [
        Stock(item_name="no_expiry", owner_id="U1", expiry_date=None, status=1, created_at=fixed_now),
        Stock(item_name="expired", owner_id="U1", expiry_date=datetime(2025, 1, 8), status=1, created_at=fixed_now),
        Stock(item_name="today", owner_id="U1", expiry_date=datetime(2025, 1, 9), status=1, created_at=fixed_now),
        Stock(item_name="soon", owner_id="U1", expiry_date=datetime(2025, 1, 12), status=1, created_at=fixed_now),
    ]

    line_user_repository = DummyLineUserRepository([line_user], [web_user])
    stock_repository = DummyStockRepository(stocks)
    line_response_service = DummyLineResponseService()

    use_case = CheckExpiredStockUseCase(
        line_user_repository=line_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert line_response_service.pushes == ["U1"]
    joined = "\n".join(line_response_service.messages)
    assert "no_expiry" in joined
    assert "expired" in joined and "x" in joined
    assert "today" in joined and "今日まで" in joined
    assert "soon" in joined and "あと" in joined
