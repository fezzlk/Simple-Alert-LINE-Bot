from datetime import datetime

from werkzeug.exceptions import BadRequest

from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.UseCases.Interface.IUseCase import IUseCase


class UpdateHabitTaskLogUseCase(IUseCase):
    def __init__(self, habit_task_repository, habit_task_log_repository):
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository

    def execute(self, page_contents):
        form = page_contents.request.form
        task_id = form.get("task_id", "").strip()
        log_id = form.get("log_id", "").strip()
        scheduled_date = form.get("scheduled_date", "").strip()
        result = form.get("result", "").strip()
        note = form.get("note", "").strip()

        if not task_id or not scheduled_date or result not in ("done", "not_done", "other"):
            raise BadRequest("入力が不正です。")

        login_user = page_contents.login_user
        owner_ids = [login_user._id]
        if login_user.linked_line_user_id:
            owner_ids.append(login_user.linked_line_user_id)

        tasks = self._habit_task_repository.find({"_id": task_id})
        if not tasks or tasks[0].owner_id not in owner_ids:
            raise BadRequest("タスクが見つかりません。")

        task = tasks[0]

        if log_id:
            self._habit_task_log_repository.update(
                query={"_id": log_id},
                new_values={"result": result, "note": note or None, "recorded_at": datetime.now()},
            )
        else:
            existing = self._habit_task_log_repository.find(
                {"habit_task_id": task_id, "scheduled_date": scheduled_date}
            )
            if existing:
                self._habit_task_log_repository.update(
                    query={"_id": existing[0]._id},
                    new_values={"result": result, "note": note or None, "recorded_at": datetime.now()},
                )
            else:
                self._habit_task_log_repository.create(
                    HabitTaskLog(
                        habit_task_id=task_id,
                        owner_id=task.owner_id,
                        task_name_snapshot=task.task_name,
                        scheduled_date=scheduled_date,
                        result=result,
                        note=note or None,
                        recorded_at=datetime.now(),
                    )
                )
        return task.task_name
