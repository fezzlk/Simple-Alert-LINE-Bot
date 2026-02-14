from src.UseCases.Interface.IUseCase import IUseCase


class ViewHabitTaskLogUseCase(IUseCase):
    def __init__(self, habit_task_repository, habit_task_log_repository):
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository

    def execute(self, page_contents, task_id: str):
        page_contents.page_title = "習慣タスク実績"
        tasks = self._habit_task_repository.find({"_id": task_id})
        page_contents.data.task = tasks[0] if len(tasks) != 0 else None
        page_contents.data.logs = self._habit_task_log_repository.find(
            {"habit_task_id": task_id},
            sort=[("scheduled_date", "desc"), ("created_at", "desc")],
        )
        return page_contents
