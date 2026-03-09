from datetime import datetime

from werkzeug.exceptions import BadRequest

from src.UseCases.Interface.IUseCase import IUseCase


class UpdateHabitTaskUseCase(IUseCase):
    def __init__(self, habit_task_repository):
        self._habit_task_repository = habit_task_repository

    def execute(self, page_contents):
        form = page_contents.request.form
        task_id = form.get("task_id", "").strip()
        if not task_id:
            raise BadRequest("タスクIDが指定されていません。")

        login_user = page_contents.login_user
        owner_ids = [login_user._id]
        if login_user.linked_line_user_id:
            owner_ids.append(login_user.linked_line_user_id)

        tasks = self._habit_task_repository.find({"_id": task_id, "is_active": True})
        if not tasks or tasks[0].owner_id not in owner_ids:
            raise BadRequest("タスクが見つかりません。")

        new_values = {}
        task_name = form.get("task_name", "").strip()
        if task_name:
            new_values["task_name"] = task_name

        notify_time = form.get("notify_time", "").strip()
        if notify_time:
            try:
                datetime.strptime(notify_time, "%H:%M")
                new_values["notify_time"] = notify_time
            except ValueError:
                raise BadRequest("通知時刻は HH:MM 形式で入力してください。")

        if not new_values:
            raise BadRequest("変更内容がありません。")

        self._habit_task_repository.update(
            query={"_id": task_id},
            new_values=new_values,
        )
        return tasks[0].task_name
