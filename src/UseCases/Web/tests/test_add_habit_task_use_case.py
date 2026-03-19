from datetime import time, datetime
from types import SimpleNamespace

import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import ImmutableMultiDict

from src.Domains.Entities.HabitTask import VALID_FREQUENCIES
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Web.AddHabitTaskUseCase import AddHabitTaskUseCase


class DummyHabitTaskRepository:
    def __init__(self):
        self.created_tasks = []

    def create(self, task):
        task._id = task._id or f"T{len(self.created_tasks) + 1}"
        self.created_tasks.append(task)
        return task

    def find(self, query=None, sort=None):
        return self.created_tasks


class DummyPageContents:
    def __init__(self, form_data, login_user=None):
        self.request = SimpleNamespace(
            form=ImmutableMultiDict(form_data),
        )
        self.login_user = login_user or WebUser(
            _id="W1",
            web_user_name="test_user",
            web_user_email="test@example.com",
        )


# ---------------------------------------------------------------------------
# Valid frequency creation
# ---------------------------------------------------------------------------

class TestCreateWithValidFrequency:
    """Can create a task with each valid frequency value."""

    def test_create_daily(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "毎日タスク",
            "notify_time": "08:00",
            "frequency": "daily",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        result = use_case.execute(page)
        assert result == "毎日タスク"
        assert repo.created_tasks[0].frequency == "daily"

    def test_create_every_other_day(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "隔日タスク",
            "notify_time": "09:00",
            "frequency": "every_other_day",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        result = use_case.execute(page)
        assert result == "隔日タスク"
        assert repo.created_tasks[0].frequency == "every_other_day"
        assert repo.created_tasks[0].notify_day_of_week is None
        assert repo.created_tasks[0].notify_day_of_month is None

    def test_create_every_two_days(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "2日おきタスク",
            "notify_time": "10:00",
            "frequency": "every_two_days",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        result = use_case.execute(page)
        assert result == "2日おきタスク"
        assert repo.created_tasks[0].frequency == "every_two_days"
        assert repo.created_tasks[0].notify_day_of_week is None
        assert repo.created_tasks[0].notify_day_of_month is None

    def test_create_weekly_with_day_of_week(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "週次タスク",
            "notify_time": "09:00",
            "frequency": "weekly",
            "notify_day_of_week": "2",
            "notify_day_of_month": "",
        })
        result = use_case.execute(page)
        assert result == "週次タスク"
        assert repo.created_tasks[0].frequency == "weekly"
        assert repo.created_tasks[0].notify_day_of_week == 2

    def test_create_monthly_with_day_of_month(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "月次タスク",
            "notify_time": "12:00",
            "frequency": "monthly",
            "notify_day_of_week": "",
            "notify_day_of_month": "15",
        })
        result = use_case.execute(page)
        assert result == "月次タスク"
        assert repo.created_tasks[0].frequency == "monthly"
        assert repo.created_tasks[0].notify_day_of_month == 15


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidationErrors:
    """Weekly requires day_of_week, monthly requires day_of_month."""

    def test_weekly_without_day_of_week_raises_bad_request(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "週次タスク",
            "notify_time": "09:00",
            "frequency": "weekly",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        with pytest.raises(BadRequest, match="曜日"):
            use_case.execute(page)

    def test_monthly_without_day_of_month_raises_bad_request(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "月次タスク",
            "notify_time": "12:00",
            "frequency": "monthly",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        with pytest.raises(BadRequest, match="日"):
            use_case.execute(page)

    def test_missing_task_name_raises_bad_request(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "",
            "notify_time": "09:00",
            "frequency": "daily",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        with pytest.raises(BadRequest):
            use_case.execute(page)


# ---------------------------------------------------------------------------
# Invalid frequency defaults to daily
# ---------------------------------------------------------------------------

class TestInvalidFrequency:
    """Invalid frequency value should fall back to 'daily'."""

    def test_invalid_frequency_defaults_to_daily(self):
        repo = DummyHabitTaskRepository()
        use_case = AddHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_name": "テスト",
            "notify_time": "08:00",
            "frequency": "invalid_frequency",
            "notify_day_of_week": "",
            "notify_day_of_month": "",
        })
        result = use_case.execute(page)
        assert result == "テスト"
        assert repo.created_tasks[0].frequency == "daily"
