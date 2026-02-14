from datetime import datetime

from werkzeug.exceptions import BadRequest

from src.Domains.Entities.HabitTask import HabitTask
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

        notify_time = form.notify_time.data.strftime("%H:%M")
        task = HabitTask(
            owner_id=page_contents.login_user._id,
            task_name=form.task_name.data,
            frequency="daily",
            notify_time=notify_time,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._habit_task_repository.create(task)
        return task.task_name
