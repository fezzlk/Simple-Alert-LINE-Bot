from datetime import datetime

from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase


class DummyLineUserRepository(ILineUserRepository):
    def __init__(self, line_users: list[LineUser]):
        self._line_users = line_users

    def create(self, new_line_user: LineUser) -> LineUser:
        return new_line_user

    def update(self, query, new_line_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query: dict = None) -> list[LineUser]:
        return self._line_users if not query else []


class DummyWebUserRepository(IWebUserRepository):
    def __init__(self, web_users: list[WebUser]):
        self._web_users = web_users

    def create(self, new_web_user: WebUser) -> WebUser:
        return new_web_user

    def update(self, query, new_web_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query: dict = None) -> list[WebUser]:
        if not query:
            return self._web_users
        linked_id = query.get("linked_line_user_id")
        required_linked = query.get("is_linked_line_user")
        return [
            w for w in self._web_users
            if w.linked_line_user_id == linked_id and w.is_linked_line_user == required_linked
        ]


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
        Stock(item_name="no_expiry", owner_id="U1", expiry_date=None, status=1, notify_enabled=True, created_at=fixed_now),
        Stock(item_name="expired", owner_id="U1", expiry_date=datetime(2025, 1, 8), status=1, created_at=fixed_now),
        Stock(item_name="today", owner_id="U1", expiry_date=datetime(2025, 1, 10), status=1, created_at=fixed_now),
        Stock(item_name="tomorrow", owner_id="U1", expiry_date=datetime(2025, 1, 11), status=1, created_at=fixed_now),
        Stock(item_name="three_days", owner_id="U1", expiry_date=datetime(2025, 1, 13), status=1, notify_enabled=True, created_at=fixed_now),
        Stock(item_name="future", owner_id="U1", expiry_date=datetime(2025, 1, 20), status=1, notify_enabled=True, created_at=fixed_now),
    ]

    line_user_repository = DummyLineUserRepository([line_user])
    web_user_repository = DummyWebUserRepository([web_user])
    stock_repository = DummyStockRepository(stocks)
    line_response_service = DummyLineResponseService()

    use_case = CheckExpiredStockUseCase(
        line_user_repository=line_user_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert line_response_service.pushes == ["U1"]
    joined = "\n".join(line_response_service.messages)
    assert "webで一覧を確認" in joined
    assert "期限が3日以内のもの" in joined
    assert "today: 今日まで" in joined
    assert "tomorrow: 明日まで" in joined
    assert "three_days: あと3日" in joined
    assert "通知ONのアイテム" in joined
    assert "no_expiry" in joined
    assert "future" in joined
    assert "expired" not in joined


def test_check_expired_stock_does_not_push_when_no_active_stocks():
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
    line_user_repository = DummyLineUserRepository([line_user])
    web_user_repository = DummyWebUserRepository([web_user])
    stock_repository = DummyStockRepository([
        Stock(item_name="far", owner_id="U1", expiry_date=datetime(2025, 1, 30), status=1),
        Stock(item_name="none", owner_id="U1", expiry_date=None, status=1),
    ])
    line_response_service = DummyLineResponseService()

    use_case = CheckExpiredStockUseCase(
        line_user_repository=line_user_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert line_response_service.pushes == []
    assert line_response_service.messages == []
