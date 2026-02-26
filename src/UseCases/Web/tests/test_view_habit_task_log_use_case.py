from datetime import datetime

from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.UseCases.Web.ViewHabitTaskLogUseCase import ViewHabitTaskLogUseCase
from src.models.PageContents import HabitTaskLogListData, PageContents
from src.Domains.Entities.WebUser import WebUser


class DummyHabitTaskRepository:
    def __init__(self, tasks):
        self._tasks = tasks

    def find(self, query=None, sort=None):
        if not query:
            return self._tasks
        if "_id" in query:
            return [t for t in self._tasks if t._id == query["_id"]]
        return self._tasks


class DummyHabitTaskLogRepository:
    def __init__(self, logs):
        self._logs = logs

    def find(self, query=None, sort=None):
        if not query:
            return self._logs
        result = self._logs
        for key, value in query.items():
            result = [log for log in result if getattr(log, key) == value]
        return result


def test_view_habit_task_log_use_case_builds_calendar(dummy_app):
    with dummy_app.test_request_context():
        task = HabitTask(_id="T1", owner_id="W1", task_name="筋トレ", notify_time="16:30")
        logs = [
            HabitTaskLog(
                _id="L1",
                habit_task_id="T1",
                owner_id="W1",
                scheduled_date="2026-02-14",
                result="done",
                note="完了",
                recorded_at=datetime(2026, 2, 14, 16, 30),
            ),
            HabitTaskLog(
                _id="L2",
                habit_task_id="T1",
                owner_id="W1",
                scheduled_date="2026-02-15",
                result="not_done",
                note="未実施",
                recorded_at=datetime(2026, 2, 15, 16, 30),
            ),
        ]
        page_contents = PageContents(
            session={
                "login_user": WebUser(
                    _id="W1",
                    web_user_name="web",
                    web_user_email="web@example.com",
                    is_linked_line_user=False,
                )
            },
            request=dummy_app.test_request_context().request,
            DataClass=HabitTaskLogListData,
        )

        use_case = ViewHabitTaskLogUseCase(
            habit_task_repository=DummyHabitTaskRepository([task]),
            habit_task_log_repository=DummyHabitTaskLogRepository(logs),
        )

        result = use_case.execute(page_contents=page_contents, task_id="T1", month="2026-02")

        assert result.data.calendar_month == "2026-02"
        assert result.data.calendar_month_label == "2026年02月"
        statuses = [cell["status"] for week in result.data.calendar_weeks for cell in week]
        assert "done" in statuses
        assert "not_done" in statuses
