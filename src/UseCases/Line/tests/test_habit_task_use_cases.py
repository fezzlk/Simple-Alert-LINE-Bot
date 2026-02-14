from datetime import datetime

from src.Domains.Entities.HabitPendingConfirmation import HabitPendingConfirmation
from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Line.CheckHabitTaskUseCase import CheckHabitTaskUseCase
from src.UseCases.Line.HandleHabitTaskResponseUseCase import HandleHabitTaskResponseUseCase


class DummyLineRequestService:
    def __init__(self, user_id="U1", message=""):
        self.req_line_user_id = user_id
        self.message = message


class DummyLineResponseService:
    def __init__(self):
        self.messages = []
        self.buttons = []
        self.pushes = []

    def add_message(self, text: str):
        self.messages.append(text)

    def add_image(self, image_url: str):
        pass

    def reply(self, event):
        pass

    def push(self, to: str):
        self.pushes.append(to)
        self.buttons = []

    def reset(self):
        pass

    def push_a_message(self, to: str, message: str):
        pass


class DummyLineUserRepository:
    def __init__(self, line_users):
        self._line_users = line_users

    def find(self, query=None):
        return self._line_users if not query else []


class DummyWebUserRepository:
    def __init__(self, web_users):
        self._web_users = web_users

    def find(self, query=None):
        if not query:
            return self._web_users
        return [
            w for w in self._web_users
            if w.linked_line_user_id == query.get("linked_line_user_id")
            and w.is_linked_line_user == query.get("is_linked_line_user")
        ]


class DummyHabitTaskRepository:
    def __init__(self, tasks):
        self._tasks = tasks

    def find(self, query=None, sort=None):
        if not query:
            return self._tasks
        result = self._tasks
        if "_id" in query:
            return [t for t in self._tasks if t._id == query["_id"]]
        if "owner_id__in" in query:
            result = [t for t in result if t.owner_id in query["owner_id__in"]]
        if "is_active" in query:
            result = [t for t in result if t.is_active == query["is_active"]]
        if "frequency" in query:
            result = [t for t in result if t.frequency == query["frequency"]]
        if "notify_time" in query:
            result = [t for t in result if t.notify_time == query["notify_time"]]
        return result


class DummyHabitTaskLogRepository:
    def __init__(self):
        self._logs = []

    def create(self, new_log):
        new_log._id = new_log._id or f"L{len(self._logs) + 1}"
        self._logs.append(new_log)
        return new_log

    def find(self, query=None, sort=None):
        if not query:
            return self._logs
        result = self._logs
        for key, value in query.items():
            result = [r for r in result if getattr(r, key) == value]
        return result


class DummyHabitPendingRepository:
    def __init__(self):
        self._items = []

    def create(self, new_pending):
        new_pending._id = new_pending._id or f"P{len(self._items) + 1}"
        self._items.append(new_pending)
        return new_pending

    def find(self, query=None):
        if not query:
            return self._items
        result = self._items
        for key, value in query.items():
            result = [r for r in result if getattr(r, key) == value]
        return result

    def update(self, query, new_values):
        items = self.find(query)
        for item in items:
            for key, value in new_values.items():
                setattr(item, key, value)
        return len(items)

    def delete(self, query):
        targets = set(i._id for i in self.find(query))
        self._items = [i for i in self._items if i._id not in targets]
        return len(targets)


def test_check_habit_task_use_case_sends_confirmation(monkeypatch):
    fixed_now = datetime(2026, 2, 14, 16, 30, 0)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr("src.UseCases.Line.CheckHabitTaskUseCase.datetime", FixedDatetime)

    line_users = [LineUser(line_user_name="u1", line_user_id="U1")]
    web_users = [WebUser(_id="W1", linked_line_user_id="U1", is_linked_line_user=True)]
    tasks = [HabitTask(_id="T1", owner_id="W1", task_name="筋トレ", notify_time="16:30")]

    use_case = CheckHabitTaskUseCase(
        line_user_repository=DummyLineUserRepository(line_users),
        web_user_repository=DummyWebUserRepository(web_users),
        habit_task_repository=DummyHabitTaskRepository(tasks),
        habit_task_log_repository=DummyHabitTaskLogRepository(),
        habit_pending_confirmation_repository=DummyHabitPendingRepository(),
        line_response_service=DummyLineResponseService(),
    )
    use_case.execute()
    assert use_case._line_response_service.pushes == ["U1"]
    assert any("習慣タスク確認" in msg for msg in use_case._line_response_service.messages)


def test_handle_habit_task_response_other_flow():
    pending_repo = DummyHabitPendingRepository()
    pending_repo.create(
        HabitPendingConfirmation(
            _id="P1",
            line_user_id="U1",
            habit_task_id="T1",
            owner_id="W1",
            scheduled_date="2026-02-14",
        )
    )
    task_repo = DummyHabitTaskRepository([HabitTask(_id="T1", owner_id="W1", task_name="筋トレ")])
    log_repo = DummyHabitTaskLogRepository()

    postback_use_case = HandleHabitTaskResponseUseCase(
        line_request_service=DummyLineRequestService(user_id="U1"),
        line_response_service=DummyLineResponseService(),
        habit_task_repository=task_repo,
        habit_task_log_repository=log_repo,
        habit_pending_confirmation_repository=pending_repo,
        postback_data="habit_confirm:P1:other",
    )
    postback_use_case.execute()
    assert pending_repo.find({"_id": "P1"})[0].status == "awaiting_other_note"

    text_use_case = HandleHabitTaskResponseUseCase(
        line_request_service=DummyLineRequestService(user_id="U1", message="腰が痛いので軽め"),
        line_response_service=DummyLineResponseService(),
        habit_task_repository=task_repo,
        habit_task_log_repository=log_repo,
        habit_pending_confirmation_repository=pending_repo,
    )
    text_use_case.execute()
    assert len(log_repo.find()) == 1
    assert log_repo.find()[0].result == "other"
    assert log_repo.find()[0].note == "腰が痛いので軽め"
