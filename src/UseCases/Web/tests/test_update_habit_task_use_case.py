from datetime import datetime
from types import SimpleNamespace

import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import ImmutableMultiDict

from src.Domains.Entities.HabitTask import HabitTask, VALID_FREQUENCIES
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Web.UpdateHabitTaskUseCase import UpdateHabitTaskUseCase


class DummyHabitTaskRepository:
    def __init__(self, tasks=None):
        self._tasks = tasks or []
        self.last_query = None
        self.last_values = None

    def find(self, query=None, sort=None):
        if not query:
            return self._tasks
        result = self._tasks
        if "_id" in query:
            result = [t for t in result if t._id == query["_id"]]
        if "is_active" in query:
            result = [t for t in result if t.is_active == query["is_active"]]
        return result

    def update(self, query, new_values):
        self.last_query = query
        self.last_values = new_values
        return 1

    def create(self, task):
        return task


class DummyPageContents:
    def __init__(self, form_data, login_user=None):
        self.request = SimpleNamespace(
            form=ImmutableMultiDict(form_data),
        )
        self.login_user = login_user or WebUser(
            _id="W1",
            web_user_name="test_user",
            web_user_email="test@example.com",
            linked_line_user_id="U1",
            is_linked_line_user=True,
        )


def _existing_task(frequency="daily", notify_day_of_week=None, notify_day_of_month=None):
    return HabitTask(
        _id="T1",
        owner_id="W1",
        task_name="既存タスク",
        frequency=frequency,
        notify_time="09:00",
        is_active=True,
        notify_day_of_week=notify_day_of_week,
        notify_day_of_month=notify_day_of_month,
    )


# ---------------------------------------------------------------------------
# Update frequency to each valid value
# ---------------------------------------------------------------------------

class TestUpdateFrequency:
    """Can update frequency to each valid value."""

    def test_update_to_daily(self):
        repo = DummyHabitTaskRepository([_existing_task("weekly", notify_day_of_week=2)])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "daily",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "daily"

    def test_update_to_every_other_day(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "every_other_day",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "every_other_day"
        assert repo.last_values["notify_day_of_week"] is None
        assert repo.last_values["notify_day_of_month"] is None

    def test_update_to_every_two_days(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "every_two_days",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "every_two_days"
        assert repo.last_values["notify_day_of_week"] is None
        assert repo.last_values["notify_day_of_month"] is None

    def test_update_to_weekly_with_day_of_week(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "weekly",
            "notify_day_of_week": "4",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "weekly"
        assert repo.last_values["notify_day_of_week"] == 4
        assert repo.last_values["notify_day_of_month"] is None

    def test_update_to_monthly_with_day_of_month(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "monthly",
            "notify_day_of_month": "20",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "monthly"
        assert repo.last_values["notify_day_of_month"] == 20
        assert repo.last_values["notify_day_of_week"] is None


# ---------------------------------------------------------------------------
# Invalid frequency raises BadRequest
# ---------------------------------------------------------------------------

class TestInvalidFrequency:
    """Invalid frequency should raise BadRequest."""

    def test_invalid_frequency_raises_bad_request(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "biweekly",
        })
        with pytest.raises(BadRequest, match="無効な頻度"):
            use_case.execute(page)

    def test_another_invalid_frequency(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "yearly",
        })
        with pytest.raises(BadRequest, match="無効な頻度"):
            use_case.execute(page)


# ---------------------------------------------------------------------------
# Weekly/monthly require their specific day field
# ---------------------------------------------------------------------------

class TestRequiredDayFields:
    """Changing to weekly requires day_of_week; monthly requires day_of_month."""

    def test_weekly_without_day_of_week_raises_bad_request(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "weekly",
            "notify_day_of_week": "",
        })
        with pytest.raises(BadRequest, match="曜日"):
            use_case.execute(page)

    def test_monthly_without_day_of_month_raises_bad_request(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "monthly",
            "notify_day_of_month": "",
        })
        with pytest.raises(BadRequest, match="日"):
            use_case.execute(page)


# ---------------------------------------------------------------------------
# Changing from weekly/monthly to daily/new frequencies clears day fields
# ---------------------------------------------------------------------------

class TestClearDayFieldsOnFrequencyChange:
    """Changing from weekly to daily (or new frequencies) clears day_of_week/day_of_month."""

    def test_weekly_to_daily_clears_day_fields(self):
        repo = DummyHabitTaskRepository([_existing_task("weekly", notify_day_of_week=3)])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "daily",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "daily"
        assert repo.last_values["notify_day_of_week"] is None
        assert repo.last_values["notify_day_of_month"] is None

    def test_monthly_to_every_other_day_clears_day_fields(self):
        repo = DummyHabitTaskRepository([_existing_task("monthly", notify_day_of_month=15)])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "every_other_day",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "every_other_day"
        assert repo.last_values["notify_day_of_week"] is None
        assert repo.last_values["notify_day_of_month"] is None

    def test_weekly_to_every_two_days_clears_day_fields(self):
        repo = DummyHabitTaskRepository([_existing_task("weekly", notify_day_of_week=5)])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
            "frequency": "every_two_days",
        })
        use_case.execute(page)
        assert repo.last_values["frequency"] == "every_two_days"
        assert repo.last_values["notify_day_of_week"] is None
        assert repo.last_values["notify_day_of_month"] is None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Miscellaneous edge-case tests."""

    def test_missing_task_id_raises_bad_request(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "frequency": "daily",
        })
        with pytest.raises(BadRequest, match="タスクID"):
            use_case.execute(page)

    def test_no_changes_raises_bad_request(self):
        repo = DummyHabitTaskRepository([_existing_task()])
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T1",
        })
        with pytest.raises(BadRequest, match="変更内容"):
            use_case.execute(page)

    def test_task_not_found_raises_bad_request(self):
        repo = DummyHabitTaskRepository([])  # no tasks
        use_case = UpdateHabitTaskUseCase(habit_task_repository=repo)
        page = DummyPageContents({
            "task_id": "T_NONEXISTENT",
            "frequency": "daily",
        })
        with pytest.raises(BadRequest, match="タスクが見つかりません"):
            use_case.execute(page)
