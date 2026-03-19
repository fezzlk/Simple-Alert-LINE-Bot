from datetime import datetime
from zoneinfo import ZoneInfo

from linebot.models import ButtonsTemplate, PostbackAction, TemplateSendMessage

from src.Domains.Entities.HabitPendingConfirmation import HabitPendingConfirmation
from src.UseCases.Interface.IUseCase import IUseCase


class CheckHabitTaskUseCase(IUseCase):
    _notify_timezone = ZoneInfo("Asia/Tokyo")

    def __init__(
        self,
        line_user_repository,
        web_user_repository,
        habit_task_repository,
        habit_task_log_repository,
        habit_pending_confirmation_repository,
        line_response_service,
    ):
        self._line_user_repository = line_user_repository
        self._web_user_repository = web_user_repository
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository
        self._habit_pending_confirmation_repository = habit_pending_confirmation_repository
        self._line_response_service = line_response_service

    def execute(self) -> None:
        now = datetime.now(self._notify_timezone)
        now_hhmm = now.strftime("%H:%M")
        today_weekday = now.weekday()        # 0=Monday, 6=Sunday
        today_day_of_month = now.day
        scheduled_date = now.strftime("%Y-%m-%d")

        line_users = self._line_user_repository.find()
        for line_user in line_users:
            web_users = self._web_user_repository.find(
                {
                    "linked_line_user_id": line_user.line_user_id,
                    "is_linked_line_user": True,
                }
            )
            linked_web_user_id = web_users[0]._id if len(web_users) != 0 else ""

            all_time_tasks = self._habit_task_repository.find(
                {
                    "owner_id__in": [line_user.line_user_id, linked_web_user_id],
                    "is_active": True,
                    "notify_time": now_hhmm,
                }
            )
            tasks = []
            for task in all_time_tasks:
                if task.frequency == "daily":
                    tasks.append(task)
                elif task.frequency == "every_other_day":
                    if task.created_at:
                        delta = (now.date() - task.created_at.date()).days if hasattr(task.created_at, 'date') else (now.date() - task.created_at).days
                        if delta % 2 == 0:
                            tasks.append(task)
                    else:
                        tasks.append(task)
                elif task.frequency == "every_two_days":
                    if task.created_at:
                        delta = (now.date() - task.created_at.date()).days if hasattr(task.created_at, 'date') else (now.date() - task.created_at).days
                        if delta % 3 == 0:
                            tasks.append(task)
                    else:
                        tasks.append(task)
                elif task.frequency == "weekly" and task.notify_day_of_week == today_weekday:
                    tasks.append(task)
                elif task.frequency == "monthly" and task.notify_day_of_month == today_day_of_month:
                    tasks.append(task)

            pushed_count = 0
            for task in tasks:
                logs = self._habit_task_log_repository.find(
                    {"habit_task_id": task._id, "scheduled_date": scheduled_date}
                )
                if len(logs) != 0:
                    continue

                pendings = self._habit_pending_confirmation_repository.find(
                    {
                        "line_user_id": line_user.line_user_id,
                        "habit_task_id": task._id,
                        "scheduled_date": scheduled_date,
                    }
                )
                if len(pendings) != 0:
                    continue

                pending = self._habit_pending_confirmation_repository.create(
                    HabitPendingConfirmation(
                        line_user_id=line_user.line_user_id,
                        habit_task_id=task._id,
                        owner_id=task.owner_id,
                        scheduled_date=scheduled_date,
                        status="awaiting_answer",
                    )
                )
                self._line_response_service.add_message(
                    f'習慣タスク確認: "{task.task_name}" を実施しましたか？'
                )
                self._line_response_service.buttons.append(
                    TemplateSendMessage(
                        alt_text="習慣タスク確認",
                        template=ButtonsTemplate(
                            text="結果を選んでください",
                            actions=[
                                PostbackAction(
                                    label="OK",
                                    data=f"habit_confirm:{pending._id}:done",
                                ),
                                PostbackAction(
                                    label="NG",
                                    data=f"habit_confirm:{pending._id}:not_done",
                                ),
                                PostbackAction(
                                    label="その他",
                                    data=f"habit_confirm:{pending._id}:other",
                                ),
                            ],
                        ),
                    )
                )
                pushed_count += 1

            if pushed_count != 0:
                self._line_response_service.push(to=line_user.line_user_id)
