from calendar import Calendar
from datetime import date, datetime

from src.UseCases.Interface.IUseCase import IUseCase


class ViewHabitTaskLogUseCase(IUseCase):
    def __init__(self, habit_task_repository, habit_task_log_repository):
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository

    def _parse_target_month(self, month: str | None) -> date:
        if month:
            try:
                dt = datetime.strptime(month, "%Y-%m")
                return date(dt.year, dt.month, 1)
            except ValueError:
                pass
        today = date.today()
        return date(today.year, today.month, 1)

    def _shift_month(self, base: date, delta: int) -> date:
        year = base.year
        month = base.month + delta
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        return date(year, month, 1)

    def execute(self, page_contents, task_id: str, month: str | None = None):
        page_contents.page_title = "習慣タスク実績"
        tasks = self._habit_task_repository.find({"_id": task_id})
        page_contents.data.task = tasks[0] if len(tasks) != 0 else None
        page_contents.data.logs = self._habit_task_log_repository.find(
            {"habit_task_id": task_id},
            sort=[("scheduled_date", "desc"), ("created_at", "desc")],
        )

        target_month = self._parse_target_month(month)
        log_by_date = {}
        for log in page_contents.data.logs:
            if log.scheduled_date not in log_by_date:
                log_by_date[log.scheduled_date] = log

        weeks = []
        calendar = Calendar(firstweekday=6)
        for week in calendar.monthdatescalendar(target_month.year, target_month.month):
            week_cells = []
            for d in week:
                date_str = d.strftime("%Y-%m-%d")
                log = log_by_date.get(date_str)
                status = "none" if log is None else (log.result or "none")
                week_cells.append(
                    {
                        "date_str": date_str,
                        "day": d.day,
                        "is_current_month": d.month == target_month.month,
                        "status": status,
                        "note": "" if log is None else (log.note or ""),
                    }
                )
            weeks.append(week_cells)

        prev_month = self._shift_month(target_month, -1)
        next_month = self._shift_month(target_month, 1)
        page_contents.data.calendar_weeks = weeks
        page_contents.data.calendar_month = target_month.strftime("%Y-%m")
        page_contents.data.calendar_month_label = target_month.strftime("%Y年%m月")
        page_contents.data.prev_month = prev_month.strftime("%Y-%m")
        page_contents.data.next_month = next_month.strftime("%Y-%m")
        return page_contents
