from datetime import date

from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Line.SendWeeklyHabitCalendarUseCase import SendWeeklyHabitCalendarUseCase


class DummyLineResponseService:
    def __init__(self):
        self.images = []
        self.pushes = []

    def add_message(self, text: str):
        pass

    def add_image(self, image_url: str):
        self.images.append(image_url)

    def reply(self, event):
        pass

    def push(self, to: str):
        self.pushes.append(to)

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
        if "owner_id__in" in query:
            result = [t for t in result if t.owner_id in query["owner_id__in"]]
        if "is_active" in query:
            result = [t for t in result if t.is_active == query["is_active"]]
        return result


def test_send_weekly_habit_calendar_skips_user_without_active_tasks():
    line_users = [LineUser(line_user_name="u1", line_user_id="U1")]
    web_users = []
    tasks = []  # no active habit tasks for U1

    response_service = DummyLineResponseService()
    use_case = SendWeeklyHabitCalendarUseCase(
        line_user_repository=DummyLineUserRepository(line_users),
        web_user_repository=DummyWebUserRepository(web_users),
        habit_task_repository=DummyHabitTaskRepository(tasks),
        line_response_service=response_service,
    )
    use_case.execute()

    assert response_service.images == []
    assert response_service.pushes == []


def test_send_weekly_habit_calendar_sends_image_for_user_with_active_tasks(monkeypatch):
    fixed_today = date(2026, 3, 15)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return fixed_today

    monkeypatch.setattr(
        "src.UseCases.Line.SendWeeklyHabitCalendarUseCase.date", FixedDate
    )
    monkeypatch.setattr(
        "src.UseCases.Line.SendWeeklyHabitCalendarUseCase.config.SERVER_URL",
        "https://example.com",
    )

    line_users = [LineUser(line_user_name="u1", line_user_id="U1")]
    web_users = [WebUser(_id="W1", linked_line_user_id="U1", is_linked_line_user=True)]
    tasks = [HabitTask(_id="T1", owner_id="W1", task_name="筋トレ", is_active=True)]

    response_service = DummyLineResponseService()
    use_case = SendWeeklyHabitCalendarUseCase(
        line_user_repository=DummyLineUserRepository(line_users),
        web_user_repository=DummyWebUserRepository(web_users),
        habit_task_repository=DummyHabitTaskRepository(tasks),
        line_response_service=response_service,
    )
    use_case.execute()

    assert response_service.pushes == ["U1"]
    assert len(response_service.images) == 1
    image_url = response_service.images[0]
    assert image_url.startswith("https://example.com/_api/v1/habit_calendar/")
    assert image_url.endswith(".png")
    # トークン部分に "." (payload.signature) の区切りが含まれていること
    token_part = image_url[len("https://example.com/_api/v1/habit_calendar/"):-len(".png")]
    assert "." in token_part
