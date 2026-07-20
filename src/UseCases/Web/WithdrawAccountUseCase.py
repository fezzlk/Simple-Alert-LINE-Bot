import logging
from typing import Dict, List, Optional

from src.UseCases.Interface.IUseCase import IUseCase

logger = logging.getLogger(__name__)


class WithdrawAccountUseCase(IUseCase):
    """アカウント退会（全データ物理削除）を実行するユースケース。

    Web ログイン中ユーザーの ``web_user_id`` と、紐づく LINE ユーザーの
    ``linked_line_user_id`` を受け取り、当該ユーザーに関連する全コレクションの
    ドキュメントを owner 単位で削除する。削除件数の内訳を辞書で返す。

    削除対象:
      - stocks / habit_tasks / habit_task_logs（owner_id が LINE/Web いずれか）
      - habit_pending_confirmations（owner_id / line_user_id）
      - line_pending_operations（doc id = line_user_id）
      - notification_schedules（doc id = line_user_id）
      - line_users（line_user_id）/ web_users（_id）
    """

    def __init__(
        self,
        stock_repository,
        habit_task_repository,
        habit_task_log_repository,
        habit_pending_confirmation_repository,
        notification_schedule_repository,
        line_user_repository,
        web_user_repository,
        pending_line_operation_service,
    ):
        self._stock_repository = stock_repository
        self._habit_task_repository = habit_task_repository
        self._habit_task_log_repository = habit_task_log_repository
        self._habit_pending_confirmation_repository = habit_pending_confirmation_repository
        self._notification_schedule_repository = notification_schedule_repository
        self._line_user_repository = line_user_repository
        self._web_user_repository = web_user_repository
        self._pending_line_operation_service = pending_line_operation_service

    def execute(
        self,
        web_user_id: str,
        linked_line_user_id: Optional[str] = None,
    ) -> Dict[str, int]:
        if not web_user_id:
            raise ValueError("web_user_id is required")

        owner_ids: List[str] = [
            oid for oid in (linked_line_user_id, web_user_id) if oid
        ]

        deleted: Dict[str, int] = {}

        # ユーザーが作成したデータ（owner_id は LINE / Web いずれかを取り得る）
        deleted["stocks"] = self._stock_repository.delete({"owner_id__in": owner_ids})
        deleted["habit_tasks"] = self._habit_task_repository.delete(
            {"owner_id__in": owner_ids}
        )
        deleted["habit_task_logs"] = self._habit_task_log_repository.delete(
            {"owner_id__in": owner_ids}
        )

        # 保留中の習慣確認（owner_id と line_user_id の両軸で削除）
        pending = self._habit_pending_confirmation_repository.delete(
            {"owner_id__in": owner_ids}
        )
        if linked_line_user_id:
            pending += self._habit_pending_confirmation_repository.delete(
                {"line_user_id": linked_line_user_id}
            )
        deleted["habit_pending_confirmations"] = pending

        # LINE 由来の一時データ（いずれも doc id = line_user_id）
        if linked_line_user_id:
            self._pending_line_operation_service.clear(linked_line_user_id)
            deleted["notification_schedules"] = (
                self._notification_schedule_repository.delete_by_line_user_id(
                    linked_line_user_id
                )
            )
            deleted["line_users"] = self._line_user_repository.delete(
                {"line_user_id": linked_line_user_id}
            )
        else:
            deleted["notification_schedules"] = 0
            deleted["line_users"] = 0

        # 最後に本人アカウント
        deleted["web_users"] = self._web_user_repository.delete({"_id": web_user_id})

        logger.info(
            "Account withdrawal completed for web_user_id=%s (line_user_id=%s): %s",
            web_user_id,
            linked_line_user_id,
            deleted,
        )
        return deleted
