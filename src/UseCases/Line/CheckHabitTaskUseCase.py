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

            tasks = self._habit_task_repository.find(
                {
                    "owner_id__in": [line_user.line_user_id, linked_web_user_id],
                    "is_active": True,
                    "frequency": "daily",
                    "notify_time": now_hhmm,
                }
            )

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
