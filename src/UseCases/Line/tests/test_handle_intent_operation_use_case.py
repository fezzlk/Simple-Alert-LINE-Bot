from datetime import datetime
from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.Domains.Entities.Stock import Stock
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Line.HandleIntentOperationUseCase import HandleIntentOperationUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class DummyLineRequestService(ILineRequestService):
    def __init__(self, message: str, req_line_user_id: str = "U1"):
        self._message = message
        self._event_type = "message"
        self._req_line_user_name = "dummy"
        self._req_line_user_id = req_line_user_id
        self._req_line_group_id = None

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

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
        self.buttons = []

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


class DummyStockRepository(IStockRepository):
    def __init__(self):
        self.created = None
        self.updated_query = None
        self.updated_values = None
        self.update_count = 1
        self.found_stocks = []

    def create(self, new_stock: Stock) -> Stock:
        if new_stock._id is None:
            new_stock._id = "S1"
        self.created = new_stock
        self.found_stocks = [new_stock]
        return new_stock

    def update(self, query, new_values) -> int:
        self.updated_query = query
        self.updated_values = new_values
        return self.update_count

    def delete(self, query) -> int:
        return 0

    def find(self, query=None, sort=None) -> list[Stock]:
        return self.found_stocks


class DummyIntentParserService:
    def __init__(self, parsed):
        self.parsed = parsed

    def parse(self, message: str):
        return self.parsed


class DummyPendingOperationService:
    def __init__(self):
        self.store = {}

    def save(self, line_user_id: str, operation):
        self.store[line_user_id] = {"operation": operation}

    def get(self, line_user_id: str):
        return self.store.get(line_user_id)

    def clear(self, line_user_id: str):
        self.store.pop(line_user_id, None)


def test_register_requires_confirmation_then_execute():
    req = DummyLineRequestService(message="牛乳")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "register", "item_name": "牛乳", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    assert repo.created is None
    assert len(res.buttons) == 1

    req.message = "はい"
    use_case.execute()
    assert isinstance(repo.created, Stock)
    assert repo.created.item_name == "牛乳"


def test_delete_intent_updates_status():
    req = DummyLineRequestService(message="削除 牛乳")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "delete", "item_name": "牛乳", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.updated_query["item_name"] == "牛乳"
    assert repo.updated_values["status"] == 2


def test_register_with_expiry_date_executes_with_date():
    req = DummyLineRequestService(message="確定申告は3/15まで")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "register", "item_name": "確定申告", "expiry_date": "2026-03-15"}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.created is not None
    assert repo.created.item_name == "確定申告"
    assert repo.created.expiry_date.strftime("%Y-%m-%d") == "2026-03-15"


def test_register_without_expiry_prompts_for_followup_expiry():
    req = DummyLineRequestService(message="卵")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "register", "item_name": "卵", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.created is not None
    assert any("期限も登録しますか" in message for message in res.messages)
    assert pending.get("U1")["operation"]["intent"] == "update_recent_expiry"


class DummyHabitTaskRepository:
    def __init__(self):
        self.created = None
        self.updated_query = None
        self.updated_values = None
        self.update_count = 1
        self.found_tasks = []

    def create(self, habit_task: HabitTask) -> HabitTask:
        self.created = habit_task
        return habit_task

    def update(self, query, new_values) -> int:
        self.updated_query = query
        self.updated_values = new_values
        return self.update_count

    def find(self, query=None) -> list:
        return self.found_tasks


class DummyNotificationScheduleRepository:
    def __init__(self, current=None):
        self.current = current
        self.upsert_kwargs = None

    def find_by_line_user_id(self, line_user_id: str):
        return self.current

    def upsert(self, **kwargs):
        self.upsert_kwargs = kwargs


class DummyHabitTaskLogRepository:
    def __init__(self):
        self.created = None
        self.updated_query = None
        self.updated_values = None
        self.found_logs = []

    def create(self, log: HabitTaskLog) -> HabitTaskLog:
        self.created = log
        return log

    def update(self, query, new_values) -> int:
        self.updated_query = query
        self.updated_values = new_values
        return 1

    def find(self, query=None) -> list:
        return self.found_logs


def test_followup_expiry_date_updates_recently_registered_item():
    req = DummyLineRequestService(message="明日で")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "none", "item_name": None, "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    pending.save(
        "U1",
        {
            "intent": "update_recent_expiry",
            "item_name": "卵",
        },
    )
    repo.found_stocks = [Stock(_id="S1", item_name="卵", owner_id="U1", status=1)]
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()

    assert repo.updated_query == {"_id": "S1"}
    assert repo.updated_values is not None
    assert repo.updated_values["expiry_date"] is not None
    assert pending.get("U1") is None


def test_register_with_notify_enabled():
    req = DummyLineRequestService(message="通知ありで確定申告 3/15まで")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {
            "intent": "register",
            "item_name": "確定申告",
            "expiry_date": "2026-03-15",
            "notify_enabled": True,
        }
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    assert any("通知あり" in m for m in res.messages)

    req.message = "はい"
    use_case.execute()
    assert repo.created is not None
    assert repo.created.item_name == "確定申告"
    assert repo.created.notify_enabled is True


def test_register_habit_creates_habit_task():
    req = DummyLineRequestService(message="筋トレを習慣タスクとして追加")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {
            "intent": "register_habit",
            "item_name": "筋トレ",
            "expiry_date": None,
            "frequency": "daily",
            "notify_time": "09:00",
        }
    )
    pending = DummyPendingOperationService()
    habit_repo = DummyHabitTaskRepository()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
        habit_task_repository=habit_repo,
    )

    use_case.execute()
    assert any("習慣タスク" in m for m in res.messages)

    req.message = "はい"
    use_case.execute()
    assert habit_repo.created is not None
    assert habit_repo.created.task_name == "筋トレ"
    assert habit_repo.created.frequency == "daily"
    assert habit_repo.created.notify_time == "09:00"


def test_delete_with_exclude_expiry_filters_python_side():
    req = DummyLineRequestService(message="期限が3/11以外の卵を削除して")
    res = DummyLineResponseService()
    repo = DummyStockRepository()

    stock_keep = Stock(_id="S1", item_name="卵", owner_id="U1", status=1,
                       expiry_date=datetime(2026, 3, 11))
    stock_delete1 = Stock(_id="S2", item_name="卵", owner_id="U1", status=1,
                          expiry_date=datetime(2026, 3, 5))
    stock_delete2 = Stock(_id="S3", item_name="卵", owner_id="U1", status=1,
                          expiry_date=datetime(2026, 3, 20))
    repo.found_stocks = [stock_keep, stock_delete1, stock_delete2]

    parser = DummyIntentParserService(
        {
            "intent": "delete",
            "item_name": "卵",
            "expiry_date": None,
            "exclude_expiry_date": "2026-03-11",
        }
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    assert any("以外" in m for m in res.messages)

    req.message = "はい"
    # Track all update calls
    update_calls = []
    original_update = repo.update

    def tracking_update(query, new_values):
        update_calls.append((query, new_values))
        return original_update(query, new_values)

    repo.update = tracking_update
    use_case.execute()

    deleted_ids = [call[0]["_id"] for call in update_calls if "_id" in call[0]]
    assert "S2" in deleted_ids
    assert "S3" in deleted_ids
    assert "S1" not in deleted_ids
    assert any("削除しました" in m for m in res.messages)


def _make_use_case(req, res, parser, pending, repo=None, habit_repo=None, notif_repo=None, log_repo=None):
    return HandleIntentOperationUseCase(
        stock_repository=repo or DummyStockRepository(),
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
        habit_task_repository=habit_repo,
        notification_schedule_repository=notif_repo,
        habit_task_log_repository=log_repo,
    )


def test_delete_habit_deactivates_task():
    req = DummyLineRequestService(message="筋トレの習慣タスクを停止して")
    res = DummyLineResponseService()
    habit_repo = DummyHabitTaskRepository()
    parser = DummyIntentParserService(
        {"intent": "delete_habit", "item_name": "筋トレ", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, habit_repo=habit_repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert habit_repo.updated_query["task_name"] == "筋トレ"
    assert habit_repo.updated_values["is_active"] is False
    assert any("停止しました" in m for m in res.messages)


def test_update_habit_notify_time():
    req = DummyLineRequestService(message="筋トレの通知を朝8時に変更して")
    res = DummyLineResponseService()
    habit_repo = DummyHabitTaskRepository()
    parser = DummyIntentParserService(
        {"intent": "update_habit_notify_time", "item_name": "筋トレ", "notify_time": "08:00", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, habit_repo=habit_repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert habit_repo.updated_query["task_name"] == "筋トレ"
    assert habit_repo.updated_values["notify_time"] == "08:00"
    assert any("変更しました" in m for m in res.messages)


def test_update_notification_setting_off():
    req = DummyLineRequestService(message="通知をオフにして")
    res = DummyLineResponseService()
    notif_repo = DummyNotificationScheduleRepository()
    parser = DummyIntentParserService(
        {"intent": "update_notification", "item_name": None, "expiry_date": None,
         "enabled": False, "notify_time": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, notif_repo=notif_repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert notif_repo.upsert_kwargs is not None
    assert notif_repo.upsert_kwargs["enabled"] is False
    assert any("更新しました" in m for m in res.messages)


def test_update_stock_notify_on():
    req = DummyLineRequestService(message="牛乳の通知をオンにして")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "update_stock_notify", "item_name": "牛乳", "notify_enabled": True, "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, repo=repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.updated_query["item_name"] == "牛乳"
    assert repo.updated_values["notify_enabled"] is True
    assert any("更新しました" in m for m in res.messages)


def test_update_habit_log_existing():
    req = DummyLineRequestService(message="今日の筋トレをNGに修正して")
    res = DummyLineResponseService()
    habit_repo = DummyHabitTaskRepository()
    habit_repo.found_tasks = [HabitTask(_id="HT1", owner_id="U1", task_name="筋トレ", is_active=True)]
    log_repo = DummyHabitTaskLogRepository()
    existing_log = HabitTaskLog(_id="L1", habit_task_id="HT1", owner_id="U1",
                                task_name_snapshot="筋トレ", scheduled_date="2026-03-03",
                                result="done", note=None, recorded_at=datetime.now())
    log_repo.found_logs = [existing_log]
    parser = DummyIntentParserService(
        {"intent": "update_habit_log", "item_name": "筋トレ", "expiry_date": None,
         "scheduled_date": "2026-03-03", "result": "not_done", "note": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, habit_repo=habit_repo, log_repo=log_repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert log_repo.updated_query == {"_id": "L1"}
    assert log_repo.updated_values["result"] == "not_done"
    assert any("修正しました" in m for m in res.messages)


def test_update_habit_log_not_found_creates():
    req = DummyLineRequestService(message="今日の筋トレをOKに修正して")
    res = DummyLineResponseService()
    habit_repo = DummyHabitTaskRepository()
    habit_repo.found_tasks = [HabitTask(_id="HT1", owner_id="U1", task_name="筋トレ", is_active=True)]
    log_repo = DummyHabitTaskLogRepository()
    log_repo.found_logs = []  # ログが存在しない
    parser = DummyIntentParserService(
        {"intent": "update_habit_log", "item_name": "筋トレ", "expiry_date": None,
         "scheduled_date": "2026-03-03", "result": "done", "note": None}
    )
    pending = DummyPendingOperationService()
    use_case = _make_use_case(req, res, parser, pending, habit_repo=habit_repo, log_repo=log_repo)

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert log_repo.created is not None
    assert log_repo.created.result == "done"
    assert log_repo.created.habit_task_id == "HT1"
    assert any("修正しました" in m for m in res.messages)
