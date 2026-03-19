from datetime import datetime

from werkzeug.exceptions import BadRequest

from src.Domains.Entities.HabitTask import VALID_FREQUENCIES, HabitTask
from src.UseCases.Interface.IUseCase import IUseCase
from src.models.Forms.AddHabitTaskForm import AddHabitTaskForm


class AddHabitTaskUseCase(IUseCase):
    def __init__(self, habit_task_repository):
        self._habit_task_repository = habit_task_repository

    def execute(self, page_contents):
        form = AddHabitTaskForm(page_contents.request.form)
        if not form.validate():
            raise BadRequest(
                ", ".join([f"{k}: {v}" for k, v in form.errors.items()])
            )

        frequency = form.frequency.data or "daily"
        if frequency not in VALID_FREQUENCIES:
            frequency = "daily"

        notify_day_of_week = None
        notify_day_of_month = None

        if frequency == "weekly":
            dow = form.notify_day_of_week.data
            if dow is not None and dow != "":
                notify_day_of_week = int(dow)
            else:
                raise BadRequest("毎週の場合は曜日を選択してください。")
        elif frequency == "monthly":
            dom = form.notify_day_of_month.data
            if dom is not None and dom != "":
                notify_day_of_month = int(dom)
            else:
                raise BadRequest("毎月の場合は日を選択してください。")

        notify_time = form.notify_time.data.strftime("%H:%M")
        task = HabitTask(
            owner_id=page_contents.login_user._id,
            task_name=form.task_name.data,
            frequency=frequency,
            notify_time=notify_time,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            notify_day_of_week=notify_day_of_week,
            notify_day_of_month=notify_day_of_month,
        )
        self._habit_task_repository.create(task)
        return task.task_name
