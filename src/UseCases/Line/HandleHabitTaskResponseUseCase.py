from datetime import datetime

from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.UseCases.Interface.IUseCase import IUseCase


class HandleHabitTaskResponseUseCase(IUseCase):
    def __init__(
        self,
        line_request_service,
        line_response_service,
        habit_task_repository,
        habit_task_log_repository,
        habit_pending_confirmation_repository,
        postback_data: str = "",
    ):
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository
        self._habit_pending_confirmation_repository = habit_pending_confirmation_repository
        self._postback_data = postback_data

    def execute(self) -> None:
        if self._postback_data.startswith("habit_confirm:"):
            self._execute_postback()
            return
        self._execute_text()

    def _execute_postback(self) -> None:
        parts = self._postback_data.split(":")
        if len(parts) != 3:
            self._line_response_service.add_message("習慣タスクの回答形式が不正です。")
            return
        pending_id = parts[1]
        result = parts[2]
        pending_items = self._habit_pending_confirmation_repository.find({"_id": pending_id})
        if len(pending_items) == 0:
            self._line_response_service.add_message("回答対象の習慣タスクが見つかりません。")
            return

        pending = pending_items[0]
        if pending.line_user_id != self._line_request_service.req_line_user_id:
            self._line_response_service.add_message("この回答は実行できません。")
            return

        if result == "other":
            self._habit_pending_confirmation_repository.update(
                {"_id": pending._id},
                {"status": "awaiting_other_note"},
            )
            self._line_response_service.add_message("その他の内容を入力してください。")
            return

        if result not in ("done", "not_done"):
            self._line_response_service.add_message("回答が不正です。")
            return

        self._save_log_and_clear_pending(pending, result, None)
        self._line_response_service.add_message("実績を記録しました。")

    def _execute_text(self) -> None:
        line_user_id = self._line_request_service.req_line_user_id
        pendings = self._habit_pending_confirmation_repository.find(
            {"line_user_id": line_user_id, "status": "awaiting_other_note"}
        )
        if len(pendings) == 0:
            self._line_response_service.add_message("その他入力待ちの習慣タスクはありません。")
            return

        pending = pendings[0]
        note = (self._line_request_service.message or "").strip()
        if note == "":
            self._line_response_service.add_message("その他の内容を入力してください。")
            return

        self._save_log_and_clear_pending(pending, "other", note)
        self._line_response_service.add_message("その他として実績を記録しました。")

    def _save_log_and_clear_pending(self, pending, result: str, note: str) -> None:
        tasks = self._habit_task_repository.find({"_id": pending.habit_task_id})
        task_name = tasks[0].task_name if len(tasks) != 0 else "不明なタスク"
        self._habit_task_log_repository.create(
            HabitTaskLog(
                habit_task_id=pending.habit_task_id,
                owner_id=pending.owner_id,
                task_name_snapshot=task_name,
                scheduled_date=pending.scheduled_date,
                result=result,
                note=note,
                recorded_at=datetime.now(),
            )
        )
        self._habit_pending_confirmation_repository.delete({"_id": pending._id})
