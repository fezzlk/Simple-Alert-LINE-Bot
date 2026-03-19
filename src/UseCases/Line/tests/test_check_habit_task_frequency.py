from datetime import datetime

from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Line.CheckHabitTaskUseCase import CheckHabitTaskUseCase

# Re-use dummy helpers from the existing test module
from src.UseCases.Line.tests.test_habit_task_use_cases import (
    DummyHabitPendingRepository,
    DummyHabitTaskLogRepository,
    DummyHabitTaskRepository,
    DummyLineResponseService,
    DummyLineUserRepository,
    DummyWebUserRepository,
)


def _make_fixed_datetime(fixed_now):
    """Return a datetime subclass whose .now() always returns *fixed_now*."""

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    return FixedDatetime


def _run_check(monkeypatch, fixed_now, tasks):
    """Helper: run CheckHabitTaskUseCase with the given datetime and tasks."""
    monkeypatch.setattr(
        "src.UseCases.Line.CheckHabitTaskUseCase.datetime",
        _make_fixed_datetime(fixed_now),
    )

    line_users = [LineUser(line_user_name="u1", line_user_id="U1")]
    web_users = []
    response_service = DummyLineResponseService()

    use_case = CheckHabitTaskUseCase(
        line_user_repository=DummyLineUserRepository(line_users),
        web_user_repository=DummyWebUserRepository(web_users),
        habit_task_repository=DummyHabitTaskRepository(tasks),
        habit_task_log_repository=DummyHabitTaskLogRepository(),
        habit_pending_confirmation_repository=DummyHabitPendingRepository(),
        line_response_service=response_service,
    )
    use_case.execute()
    return response_service


# ---------------------------------------------------------------------------
# every_other_day – triggers on even-numbered days from created_at
# ---------------------------------------------------------------------------

class TestEveryOtherDay:
    """Tests for frequency='every_other_day' (1日おき)."""

    def test_triggers_on_day_0(self, monkeypatch):
        """Day 0 (same day as created_at) -> delta % 2 == 0 -> triggers."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 10, 9, 0, 0)  # day 0
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_triggers_on_day_2(self, monkeypatch):
        """Day 2 from created_at -> delta % 2 == 0 -> triggers."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 12, 9, 0, 0)  # day 2
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_triggers_on_day_4(self, monkeypatch):
        """Day 4 from created_at -> delta % 2 == 0 -> triggers."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 14, 9, 0, 0)  # day 4
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_does_not_trigger_on_day_1(self, monkeypatch):
        """Day 1 from created_at -> delta % 2 == 1 -> does NOT trigger."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 11, 9, 0, 0)  # day 1
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_does_not_trigger_on_day_3(self, monkeypatch):
        """Day 3 from created_at -> delta % 2 == 1 -> does NOT trigger."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 13, 9, 0, 0)  # day 3
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_does_not_trigger_on_day_5(self, monkeypatch):
        """Day 5 from created_at -> delta % 2 == 1 -> does NOT trigger."""
        created = datetime(2026, 3, 10, 8, 0, 0)
        now = datetime(2026, 3, 15, 9, 0, 0)  # day 5
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_fallback_when_no_created_at(self, monkeypatch):
        """If created_at is None, task should still trigger (fallback)."""
        now = datetime(2026, 3, 11, 9, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="隔日タスク",
                frequency="every_other_day", notify_time="09:00",
                created_at=None,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]


# ---------------------------------------------------------------------------
# every_two_days – triggers every 3rd day from created_at
# ---------------------------------------------------------------------------

class TestEveryTwoDays:
    """Tests for frequency='every_two_days' (2日おき)."""

    def test_triggers_on_day_0(self, monkeypatch):
        """Day 0 -> delta % 3 == 0 -> triggers."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 1, 10, 0, 0)  # day 0
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_triggers_on_day_3(self, monkeypatch):
        """Day 3 -> delta % 3 == 0 -> triggers."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 4, 10, 0, 0)  # day 3
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_triggers_on_day_6(self, monkeypatch):
        """Day 6 -> delta % 3 == 0 -> triggers."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 7, 10, 0, 0)  # day 6
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_does_not_trigger_on_day_1(self, monkeypatch):
        """Day 1 -> delta % 3 == 1 -> does NOT trigger."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 2, 10, 0, 0)  # day 1
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_does_not_trigger_on_day_2(self, monkeypatch):
        """Day 2 -> delta % 3 == 2 -> does NOT trigger."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 3, 10, 0, 0)  # day 2
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_does_not_trigger_on_day_4(self, monkeypatch):
        """Day 4 -> delta % 3 == 1 -> does NOT trigger."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 5, 10, 0, 0)  # day 4
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_does_not_trigger_on_day_5(self, monkeypatch):
        """Day 5 -> delta % 3 == 2 -> does NOT trigger."""
        created = datetime(2026, 3, 1, 8, 0, 0)
        now = datetime(2026, 3, 6, 10, 0, 0)  # day 5
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=created,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_fallback_when_no_created_at(self, monkeypatch):
        """If created_at is None, task should still trigger (fallback)."""
        now = datetime(2026, 3, 2, 10, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="2日おきタスク",
                frequency="every_two_days", notify_time="10:00",
                created_at=None,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]


# ---------------------------------------------------------------------------
# Existing frequencies still work correctly alongside new ones
# ---------------------------------------------------------------------------

class TestExistingFrequencies:
    """Confirm daily, weekly, monthly still behave correctly."""

    def test_daily_always_triggers(self, monkeypatch):
        now = datetime(2026, 3, 18, 8, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="毎日タスク",
                frequency="daily", notify_time="08:00",
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_weekly_triggers_on_matching_weekday(self, monkeypatch):
        # 2026-03-18 is Wednesday (weekday=2)
        now = datetime(2026, 3, 18, 9, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="週次タスク",
                frequency="weekly", notify_time="09:00",
                notify_day_of_week=2,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_weekly_does_not_trigger_on_wrong_weekday(self, monkeypatch):
        # 2026-03-18 is Wednesday (weekday=2), task is for Monday (0)
        now = datetime(2026, 3, 18, 9, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="週次タスク",
                frequency="weekly", notify_time="09:00",
                notify_day_of_week=0,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []

    def test_monthly_triggers_on_matching_day(self, monkeypatch):
        now = datetime(2026, 3, 18, 12, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="月次タスク",
                frequency="monthly", notify_time="12:00",
                notify_day_of_month=18,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == ["U1"]

    def test_monthly_does_not_trigger_on_wrong_day(self, monkeypatch):
        now = datetime(2026, 3, 18, 12, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="月次タスク",
                frequency="monthly", notify_time="12:00",
                notify_day_of_month=1,
            )
        ]
        svc = _run_check(monkeypatch, now, tasks)
        assert svc.pushes == []


# ---------------------------------------------------------------------------
# Mixed frequencies in a single run
# ---------------------------------------------------------------------------

class TestMixedFrequencies:
    """Multiple tasks with different frequencies in one execution."""

    def test_only_matching_tasks_trigger(self, monkeypatch):
        created = datetime(2026, 3, 10, 8, 0, 0)
        # 2026-03-12 is day 2 from created (even) and Thursday (weekday=3)
        now = datetime(2026, 3, 12, 9, 0, 0)
        tasks = [
            HabitTask(
                _id="T1", owner_id="U1", task_name="毎日",
                frequency="daily", notify_time="09:00",
                created_at=created,
            ),
            HabitTask(
                _id="T2", owner_id="U1", task_name="隔日",
                frequency="every_other_day", notify_time="09:00",
                created_at=created,
            ),
            HabitTask(
                _id="T3", owner_id="U1", task_name="2日おき",
                frequency="every_two_days", notify_time="09:00",
                created_at=created,
            ),  # day 2, 2 % 3 != 0 -> skip
            HabitTask(
                _id="T4", owner_id="U1", task_name="週次木曜",
                frequency="weekly", notify_time="09:00",
                notify_day_of_week=3,
            ),
        ]
        svc = _run_check(monkeypatch, now, tasks)
        # T1 (daily), T2 (every_other_day day 2), T4 (weekly Thursday) trigger
        # T3 (every_two_days day 2) does NOT
        assert svc.pushes == ["U1"]
        assert len(svc.messages) == 3  # 3 tasks triggered
