from typing import Tuple

from flask import request

from src.UseCases.Interface.IUseCase import IUseCase
from src.models.Forms.AddHabitTaskForm import AddHabitTaskForm
from src.models.PageContents import PageContents


class ViewHabitTaskListUseCase(IUseCase):
    def __init__(self, habit_task_repository):
        self._habit_task_repository = habit_task_repository

    def execute(self, page_contents: PageContents) -> Tuple[PageContents, AddHabitTaskForm]:
        page_contents.page_title = "習慣タスク"
        login_user = page_contents.login_user
        owner_ids = [login_user._id, login_user.linked_line_user_id]
        tasks = self._habit_task_repository.find(
            {
                "owner_id__in": owner_ids,
                "is_active": True,
            },
            sort=[("notify_time", "asc"), ("task_name", "asc")],
        )
        stopped_tasks = self._habit_task_repository.find(
            {
                "owner_id__in": owner_ids,
                "is_active": False,
            },
            sort=[("notify_time", "asc"), ("task_name", "asc")],
        )
        page_contents.data.tasks = tasks
        page_contents.data.stopped_tasks = stopped_tasks
        form = AddHabitTaskForm(request.form)
        return page_contents, form
