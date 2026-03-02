from datetime import datetime, timedelta
import re

from linebot.models import ButtonsTemplate, PostbackAction, TemplateSendMessage

from src.Domains.Entities.HabitTask import HabitTask
from src.Domains.Entities.HabitTaskLog import HabitTaskLog
from src.Domains.Entities.Stock import Stock
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.services.LineIntentParserService import LineIntentParserService
from src.services.PendingLineOperationService import PendingLineOperationService


class HandleIntentOperationUseCase(IUseCase):
    def __init__(
        self,
        stock_repository: IStockRepository,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
        intent_parser_service: LineIntentParserService,
        pending_operation_service: PendingLineOperationService,
        habit_task_repository=None,
        notification_schedule_repository=None,
        habit_task_log_repository=None,
    ):
        self._stock_repository = stock_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._intent_parser_service = intent_parser_service
        self._pending_operation_service = pending_operation_service
        self._habit_task_repository = habit_task_repository
        self._notification_schedule_repository = notification_schedule_repository
        self._habit_task_log_repository = habit_task_log_repository

    def execute(self) -> None:
        message = (self._line_request_service.message or "").strip()
        line_user_id = self._line_request_service.req_line_user_id
        if message == "":
            self._line_response_service.add_message("登録したいアイテム名を送ってください。")
            return

        if self._handle_recent_register_expiry_update(line_user_id, message):
            return

        if message in ("はい", "YES", "yes"):
            self._execute_pending(line_user_id)
            return
        if message in ("いいえ", "キャンセル", "NO", "no"):
            self._pending_operation_service.clear(line_user_id)
            self._line_response_service.add_message("キャンセルしました。")
            return

        parsed = self._intent_parser_service.parse(message)
        if parsed["intent"] == "none":
            self._line_response_service.add_message(
                "操作を特定できませんでした。登録/更新/削除したい内容をもう一度送ってください。"
            )
            return

        self._pending_operation_service.save(
            line_user_id,
            {
                "intent": parsed["intent"],
                "item_name": parsed["item_name"],
                "expiry_date": parsed["expiry_date"],
                "exclude_expiry_date": parsed.get("exclude_expiry_date"),
                "notify_enabled": parsed.get("notify_enabled", False),
                "frequency": parsed.get("frequency"),
                "notify_time": parsed.get("notify_time"),
                "enabled": parsed.get("enabled"),
                "scheduled_date": parsed.get("scheduled_date"),
                "result": parsed.get("result"),
                "note": parsed.get("note"),
            },
        )
        self._reply_confirmation(parsed)

    def _reply_confirmation(self, parsed):
        intent = parsed["intent"]
        item_name = parsed["item_name"]
        expiry_date = parsed["expiry_date"]
        exclude_expiry_date = parsed.get("exclude_expiry_date")
        notify_enabled = parsed.get("notify_enabled", False)
        frequency = parsed.get("frequency")
        notify_time = parsed.get("notify_time")

        if intent == "register":
            if expiry_date:
                date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                notify_suffix = "（通知あり）" if notify_enabled else ""
                message = f'"{item_name}" を期限 {date_text} で登録します{notify_suffix}。よろしいですか？'
            else:
                notify_suffix = "（通知あり）" if notify_enabled else ""
                message = f'"{item_name}" を登録します{notify_suffix}。よろしいですか？'
        elif intent == "register_habit":
            freq_text = "毎週" if frequency == "weekly" else "毎日"
            time_text = notify_time or "12:00"
            message = f'習慣タスク "{item_name}" を登録します（{freq_text} {time_text} にリマインド）。よろしいですか？'
        elif intent == "update":
            date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
            message = f'"{item_name}" の期限を {date_text} に更新します。よろしいですか？'
        elif intent == "delete":
            if exclude_expiry_date:
                excl_text = datetime.strptime(exclude_expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                message = f'"{item_name}" を削除します（{excl_text}以外の期限のもの）。よろしいですか？'
            elif expiry_date:
                date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                message = f'"{item_name}" を削除します（期限: {date_text}のもの）。よろしいですか？'
            else:
                message = f'"{item_name}" を削除します。よろしいですか？'
        elif intent == "delete_habit":
            message = f'習慣タスク "{item_name}" を停止します。よろしいですか？'
        elif intent == "update_habit_notify_time":
            message = f'習慣タスク "{item_name}" の通知時刻を {notify_time} に変更します。よろしいですか？'
        elif intent == "update_notification":
            enabled = parsed.get("enabled")
            parts = []
            if enabled is not None:
                parts.append(f"enabled={'オン' if enabled else 'オフ'}")
            if notify_time:
                parts.append(f"時刻={notify_time}")
            message = f'通知設定を変更します（{" / ".join(parts)}）。よろしいですか？'
        elif intent == "update_stock_notify":
            notify_enabled = parsed.get("notify_enabled", False)
            message = f'"{item_name}" の通知を {"オン" if notify_enabled else "オフ"} にします。よろしいですか？'
        elif intent == "update_habit_log":
            scheduled_date = parsed.get("scheduled_date")
            result = parsed.get("result")
            date_text = datetime.strptime(scheduled_date, "%Y-%m-%d").strftime("%-m月%-d日")
            result_text = {"done": "OK", "not_done": "NG", "other": "その他"}.get(result, result)
            message = f'習慣タスク "{item_name}" の {date_text} の実績を "{result_text}" に修正します。よろしいですか？'
        else:
            message = f'"{item_name}" を削除します。よろしいですか？'

        self._line_response_service.add_message(message)
        self._line_response_service.buttons.append(
            TemplateSendMessage(
                alt_text="確認",
                template=ButtonsTemplate(
                    text="実行しますか？",
                    actions=[
                        PostbackAction(label="はい", data="intent_confirm:yes"),
                        PostbackAction(label="いいえ", data="intent_confirm:no"),
                    ],
                ),
            )
        )

    def _execute_pending(self, line_user_id: str) -> None:
        pending = self._pending_operation_service.get(line_user_id)
        if not pending or not pending.get("operation"):
            self._line_response_service.add_message("確認待ちの操作はありません。")
            return

        operation = pending["operation"]
        intent = operation.get("intent")
        item_name = operation.get("item_name")
        expiry_date = operation.get("expiry_date")

        if intent == "register":
            parsed_expiry_date = (
                datetime.strptime(expiry_date, "%Y-%m-%d") if expiry_date else None
            )
            self._stock_repository.create(
                Stock(
                    item_name=item_name,
                    owner_id=line_user_id,
                    expiry_date=parsed_expiry_date,
                    status=1,
                    notify_enabled=operation.get("notify_enabled", False),
                )
            )
            if parsed_expiry_date:
                self._line_response_service.add_message(
                    f'"{item_name}" を期限{parsed_expiry_date.strftime("%Y年%m月%d日")}で登録しました。'
                )
            else:
                self._line_response_service.add_message(f'"{item_name}" を登録しました。')
                self._line_response_service.add_message(
                    '期限も登録しますか？「15日で」「明日で」「3/15で」のように送ってください。不要なら「なし」。'
                )
                self._pending_operation_service.clear(line_user_id)
                self._pending_operation_service.save(
                    line_user_id,
                    {
                        "intent": "update_recent_expiry",
                        "item_name": item_name,
                    },
                )
                return
        elif intent == "update":
            count = self._stock_repository.update(
                query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
                new_values={"expiry_date": datetime.strptime(expiry_date, "%Y-%m-%d")},
            )
            if count == 0:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            else:
                self._line_response_service.add_message(f'"{item_name}" を更新しました。')
        elif intent == "delete":
            exclude_expiry = operation.get("exclude_expiry_date")
            filter_expiry = expiry_date

            if filter_expiry or exclude_expiry:
                all_stocks = self._stock_repository.find(
                    query={"owner_id": line_user_id, "item_name": item_name, "status": 1}
                )
                if filter_expiry:
                    target_date = datetime.strptime(filter_expiry, "%Y-%m-%d").date()
                    targets = [
                        s for s in all_stocks
                        if s.expiry_date and s.expiry_date.date() == target_date
                    ]
                else:
                    exclude_date = datetime.strptime(exclude_expiry, "%Y-%m-%d").date()
                    targets = [
                        s for s in all_stocks
                        if not (s.expiry_date and s.expiry_date.date() == exclude_date)
                    ]
                for s in targets:
                    self._stock_repository.update(
                        query={"_id": s._id}, new_values={"status": 2}
                    )
                count = len(targets)
            else:
                count = self._stock_repository.update(
                    query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
                    new_values={"status": 2},
                )

            if count == 0:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            else:
                self._line_response_service.add_message(f'"{item_name}" を削除しました。')
        elif intent == "register_habit":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク登録は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            frequency = operation.get("frequency") or "daily"
            notify_time = operation.get("notify_time") or "12:00"
            self._habit_task_repository.create(
                HabitTask(
                    owner_id=line_user_id,
                    task_name=item_name,
                    frequency=frequency,
                    notify_time=notify_time,
                    is_active=True,
                )
            )
            freq_text = "毎週" if frequency == "weekly" else "毎日"
            self._line_response_service.add_message(
                f'習慣タスク "{item_name}" を登録しました（{freq_text} {notify_time} にリマインド）。'
            )
        elif intent == "delete_habit":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク操作は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            count = self._habit_task_repository.update(
                query={"owner_id": line_user_id, "task_name": item_name, "is_active": True},
                new_values={"is_active": False},
            )
            if count > 0:
                self._line_response_service.add_message(f'習慣タスク "{item_name}" を停止しました。')
            else:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
        elif intent == "update_habit_notify_time":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク操作は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            notify_time = operation.get("notify_time")
            count = self._habit_task_repository.update(
                query={"owner_id": line_user_id, "task_name": item_name, "is_active": True},
                new_values={"notify_time": notify_time},
            )
            if count > 0:
                self._line_response_service.add_message(
                    f'習慣タスク "{item_name}" の通知時刻を {notify_time} に変更しました。'
                )
            else:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
        elif intent == "update_notification":
            if self._notification_schedule_repository is None:
                self._line_response_service.add_message("通知設定の変更は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            enabled = operation.get("enabled")
            notify_time = operation.get("notify_time")
            current = self._notification_schedule_repository.find_by_line_user_id(line_user_id)
            new_enabled = enabled if enabled is not None else (current.enabled if current else True)
            new_time = notify_time or (current.notify_time if current else "12:00")
            self._notification_schedule_repository.upsert(
                line_user_id=line_user_id,
                notify_time=new_time,
                enabled=new_enabled,
            )
            self._line_response_service.add_message("通知設定を更新しました。")
        elif intent == "update_stock_notify":
            count = self._stock_repository.update(
                query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
                new_values={"notify_enabled": operation.get("notify_enabled", False)},
            )
            if count > 0:
                self._line_response_service.add_message(f'"{item_name}" の通知設定を更新しました。')
            else:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
        elif intent == "update_habit_log":
            if self._habit_task_repository is None or self._habit_task_log_repository is None:
                self._line_response_service.add_message("習慣タスク操作は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            scheduled_date = operation.get("scheduled_date")
            result = operation.get("result")
            note = operation.get("note")
            tasks = self._habit_task_repository.find(
                {"owner_id": line_user_id, "task_name": item_name, "is_active": True}
            )
            if not tasks:
                self._line_response_service.add_message(f'習慣タスク "{item_name}" が見つかりませんでした。')
                self._pending_operation_service.clear(line_user_id)
                return
            task = tasks[0]
            logs = self._habit_task_log_repository.find(
                {"habit_task_id": task._id, "scheduled_date": scheduled_date}
            )
            if logs:
                self._habit_task_log_repository.update(
                    query={"_id": logs[0]._id},
                    new_values={"result": result, "note": note, "recorded_at": datetime.now()},
                )
            else:
                self._habit_task_log_repository.create(
                    HabitTaskLog(
                        habit_task_id=task._id,
                        owner_id=line_user_id,
                        task_name_snapshot=item_name,
                        scheduled_date=scheduled_date,
                        result=result,
                        note=note,
                        recorded_at=datetime.now(),
                    )
                )
            result_text = {"done": "OK", "not_done": "NG", "other": "その他"}.get(result, result)
            self._line_response_service.add_message(
                f'習慣タスク "{item_name}" の {scheduled_date} の実績を "{result_text}" に修正しました。'
            )
        else:
            self._line_response_service.add_message("操作を特定できませんでした。")

        self._pending_operation_service.clear(line_user_id)

    def _handle_recent_register_expiry_update(self, line_user_id: str, message: str) -> bool:
        pending = self._pending_operation_service.get(line_user_id)
        if not pending or not pending.get("operation"):
            return False

        operation = pending["operation"]
        if operation.get("intent") != "update_recent_expiry":
            return False

        if message in ("なし", "不要", "いらない", "NO", "no"):
            self._pending_operation_service.clear(line_user_id)
            self._line_response_service.add_message("期限なしのままにしました。")
            return True

        parsed_date = self._parse_followup_expiry_date(message)
        if parsed_date is None:
            self._line_response_service.add_message(
                '期限を解釈できませんでした。「15日で」「明日で」「3/15で」のように送ってください。'
            )
            return True

        item_name = operation.get("item_name")
        stocks = self._stock_repository.find(
            query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
            sort=[("created_at", "desc")],
        )
        if len(stocks) == 0:
            self._pending_operation_service.clear(line_user_id)
            self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            return True

        target = stocks[0]
        self._stock_repository.update(
            query={"_id": target._id},
            new_values={"expiry_date": parsed_date},
        )
        self._pending_operation_service.clear(line_user_id)
        self._line_response_service.add_message(
            f'"{item_name}" の期限を{parsed_date.strftime("%Y年%m月%d日")}に更新しました。'
        )
        return True

    def _parse_followup_expiry_date(self, message: str):
        text = message.strip()
        if text == "":
            return None

        normalized = re.sub(r"^(じゃあ|では|なら)\s*", "", text)
        normalized = re.sub(r"(で|です)$", "", normalized).strip()

        today = datetime.now()

        if normalized in ("今日",):
            return datetime(today.year, today.month, today.day)
        if normalized in ("明日",):
            next_day = today + timedelta(days=1)
            return datetime(next_day.year, next_day.month, next_day.day)

        iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", normalized)
        if iso_match:
            try:
                return datetime(
                    int(iso_match.group(1)),
                    int(iso_match.group(2)),
                    int(iso_match.group(3)),
                )
            except ValueError:
                return None

        month_day_match = re.match(r"^(\d{1,2})[/-](\d{1,2})$", normalized)
        if month_day_match:
            month = int(month_day_match.group(1))
            day = int(month_day_match.group(2))
            try:
                return datetime(today.year, month, day)
            except ValueError:
                return None

        month_day_jp_match = re.match(r"^(\d{1,2})月(\d{1,2})日$", normalized)
        if month_day_jp_match:
            month = int(month_day_jp_match.group(1))
            day = int(month_day_jp_match.group(2))
            try:
                return datetime(today.year, month, day)
            except ValueError:
                return None

        day_only_match = re.match(r"^(\d{1,2})日$", normalized)
        if day_only_match:
            day = int(day_only_match.group(1))
            try:
                if day >= today.day:
                    return datetime(today.year, today.month, day)
                if today.month == 12:
                    return datetime(today.year + 1, 1, day)
                return datetime(today.year, today.month + 1, day)
            except ValueError:
                return None

        return None
