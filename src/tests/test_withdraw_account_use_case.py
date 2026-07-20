import pytest

from src.UseCases.Web.WithdrawAccountUseCase import WithdrawAccountUseCase


class DummyRepo:
    """delete(query) の呼び出しを記録し、固定件数を返すダミーリポジトリ。"""

    def __init__(self, delete_result: int = 1):
        self.delete_result = delete_result
        self.delete_calls = []

    def delete(self, query):
        self.delete_calls.append(query)
        return self.delete_result


class DummyNotificationScheduleRepo:
    def __init__(self, result: int = 1):
        self.result = result
        self.deleted_line_user_ids = []

    def delete_by_line_user_id(self, line_user_id):
        self.deleted_line_user_ids.append(line_user_id)
        return self.result


class DummyPendingLineOperationService:
    def __init__(self):
        self.cleared = []

    def clear(self, line_user_id):
        self.cleared.append(line_user_id)


def _build(**overrides):
    repos = dict(
        stock_repository=DummyRepo(),
        habit_task_repository=DummyRepo(),
        habit_task_log_repository=DummyRepo(),
        habit_pending_confirmation_repository=DummyRepo(),
        notification_schedule_repository=DummyNotificationScheduleRepo(),
        line_user_repository=DummyRepo(),
        web_user_repository=DummyRepo(),
        pending_line_operation_service=DummyPendingLineOperationService(),
    )
    repos.update(overrides)
    return WithdrawAccountUseCase(**repos), repos


def test_requires_web_user_id():
    use_case, _ = _build()
    with pytest.raises(ValueError):
        use_case.execute(web_user_id="", linked_line_user_id="L1")


def test_deletes_all_collections_for_linked_user():
    use_case, repos = _build()

    result = use_case.execute(web_user_id="W1", linked_line_user_id="L1")

    # owner_id__in には LINE / Web 両方の ID が入る
    assert repos["stock_repository"].delete_calls[0] == {"owner_id__in": ["L1", "W1"]}
    assert repos["habit_task_repository"].delete_calls[0] == {"owner_id__in": ["L1", "W1"]}
    assert repos["habit_task_log_repository"].delete_calls[0] == {"owner_id__in": ["L1", "W1"]}

    # 習慣の保留確認は owner_id__in と line_user_id の両方で削除
    pending_calls = repos["habit_pending_confirmation_repository"].delete_calls
    assert {"owner_id__in": ["L1", "W1"]} in pending_calls
    assert {"line_user_id": "L1"} in pending_calls

    # LINE 由来の一時データ
    assert repos["pending_line_operation_service"].cleared == ["L1"]
    assert repos["notification_schedule_repository"].deleted_line_user_ids == ["L1"]
    assert repos["line_user_repository"].delete_calls[0] == {"line_user_id": "L1"}

    # 本人アカウント
    assert repos["web_user_repository"].delete_calls[0] == {"_id": "W1"}

    # 件数内訳が返る
    assert result["web_users"] == 1
    assert result["notification_schedules"] == 1


def test_web_only_user_skips_line_collections():
    use_case, repos = _build()

    result = use_case.execute(web_user_id="W1", linked_line_user_id=None)

    # owner_id__in は Web のみ
    assert repos["stock_repository"].delete_calls[0] == {"owner_id__in": ["W1"]}

    # LINE 系は呼ばれない
    assert repos["pending_line_operation_service"].cleared == []
    assert repos["notification_schedule_repository"].deleted_line_user_ids == []
    assert repos["line_user_repository"].delete_calls == []
    assert result["line_users"] == 0
    assert result["notification_schedules"] == 0

    # habit_pending は owner_id__in のみ（line_user_id では呼ばない）
    assert repos["habit_pending_confirmation_repository"].delete_calls == [
        {"owner_id__in": ["W1"]}
    ]

    # 本人アカウントは削除される
    assert repos["web_user_repository"].delete_calls[0] == {"_id": "W1"}
