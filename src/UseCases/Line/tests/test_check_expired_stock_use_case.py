from datetime import datetime, timezone

from src.Domains.Entities.NotificationSchedule import NotificationSchedule
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase


class DummyNotificationScheduleRepository:
    def __init__(self, schedules: list[NotificationSchedule]):
        self._schedules = schedules
        self.claimed_line_user_ids = []

    def find_due(self, now_utc: datetime):
        return self._schedules

    def claim_and_schedule_next(self, line_user_id: str, now_utc: datetime) -> bool:
        self.claimed_line_user_ids.append(line_user_id)
        return True


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
        linked_ids = query.get("linked_line_user_id__in", [])
        required_linked = query.get("is_linked_line_user")
        return [
            w
            for w in self._web_users
            if w.linked_line_user_id in linked_ids
            and w.is_linked_line_user == required_linked
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
        owner_ids = query.get("owner_id__in", [])
        status = query.get("status")
        return [s for s in self._stocks if s.owner_id in owner_ids and s.status == status]


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
            if tz is not None:
                return fixed_now.replace(tzinfo=timezone.utc)
            return fixed_now

    monkeypatch.setattr(
        "src.UseCases.Line.CheckExpiredStockUseCase.datetime",
        FixedDatetime,
    )

    due_schedule = NotificationSchedule(
        line_user_id="U1",
        notify_time="09:00",
        timezone="Asia/Tokyo",
        enabled=True,
        next_notify_at=datetime(2025, 1, 9, 0, 0, tzinfo=timezone.utc),
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

    notification_schedule_repository = DummyNotificationScheduleRepository([due_schedule])
    web_user_repository = DummyWebUserRepository([web_user])
    stock_repository = DummyStockRepository(stocks)
    line_response_service = DummyLineResponseService()

    use_case = CheckExpiredStockUseCase(
        notification_schedule_repository=notification_schedule_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert notification_schedule_repository.claimed_line_user_ids == ["U1"]
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


def test_check_expired_stock_does_not_push_when_no_active_stocks(monkeypatch):
    fixed_now = datetime(2025, 1, 10, 0, 0, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return fixed_now.replace(tzinfo=timezone.utc)
            return fixed_now

    monkeypatch.setattr(
        "src.UseCases.Line.CheckExpiredStockUseCase.datetime",
        FixedDatetime,
    )

    due_schedule = NotificationSchedule(
        line_user_id="U1",
        notify_time="09:00",
        timezone="Asia/Tokyo",
        enabled=True,
        next_notify_at=datetime(2025, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    web_user = WebUser(
        _id="W1",
        web_user_name="web",
        web_user_email="web@example.com",
        linked_line_user_id="U1",
        is_linked_line_user=True,
    )
    notification_schedule_repository = DummyNotificationScheduleRepository([due_schedule])
    web_user_repository = DummyWebUserRepository([web_user])
    stock_repository = DummyStockRepository(
        [
            Stock(item_name="far", owner_id="U1", expiry_date=datetime(2025, 1, 30), status=1),
            Stock(item_name="none", owner_id="U1", expiry_date=None, status=1),
        ]
    )
    line_response_service = DummyLineResponseService()

    use_case = CheckExpiredStockUseCase(
        notification_schedule_repository=notification_schedule_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert notification_schedule_repository.claimed_line_user_ids == ["U1"]
    assert line_response_service.pushes == []
    assert line_response_service.messages == []
