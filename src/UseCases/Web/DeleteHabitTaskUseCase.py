from werkzeug.exceptions import BadRequest

from src.UseCases.Interface.IUseCase import IUseCase


class DeleteHabitTaskUseCase(IUseCase):
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

        task_name = tasks[0].task_name
        self._habit_task_repository.update(
            query={"_id": task_id},
            new_values={"is_active": False},
        )
        return task_name
