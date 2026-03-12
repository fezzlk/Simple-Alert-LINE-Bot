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
        web_user_repository=None,
    ):
        self._stock_repository = stock_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._intent_parser_service = intent_parser_service
        self._pending_operation_service = pending_operation_service
        self._habit_task_repository = habit_task_repository
        self._notification_schedule_repository = notification_schedule_repository
        self._habit_task_log_repository = habit_task_log_repository
        self._web_user_repository = web_user_repository

    def _collect_existing_item_names(self, line_user_id: str) -> list:
        """ユーザーの登録済みアイテム名・習慣タスク名を収集する。"""
        names = []
        try:
            stocks = self._stock_repository.find(
                query={"owner_id": line_user_id, "status": 1}
            )
            names.extend(s.item_name for s in stocks if s.item_name)
        except Exception:
            pass
        if self._habit_task_repository is not None:
            try:
                owner_ids = self._get_habit_owner_ids(line_user_id)
                tasks = self._habit_task_repository.find(
                    {"owner_id__in": owner_ids, "is_active": True}
                )
                names.extend(t.task_name for t in tasks if t.task_name)
            except Exception:
                pass
        # 重複排除
        return list(dict.fromkeys(names))

    def _get_habit_owner_ids(self, line_user_id: str) -> list:
        """LINE user ID に紐づく Web user ID も含めた owner_id リストを返す。"""
        ids = [line_user_id]
        if self._web_user_repository is not None:
            web_users = self._web_user_repository.find(
                {"linked_line_user_id": line_user_id, "is_linked_line_user": True}
            )
            if web_users:
                ids.append(web_users[0]._id)
        return ids

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

        existing_items = self._collect_existing_item_names(line_user_id)
        parsed = self._intent_parser_service.parse(message, existing_items=existing_items)
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
                "notify_days_before": parsed.get("notify_days_before"),
                "frequency": parsed.get("frequency"),
                "notify_time": parsed.get("notify_time"),
                "notify_day_of_week": parsed.get("notify_day_of_week"),
                "notify_day_of_month": parsed.get("notify_day_of_month"),
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
        notify_days_before = parsed.get("notify_days_before")
        frequency = parsed.get("frequency")
        notify_time = parsed.get("notify_time")

        if intent == "register":
            if notify_days_before is None:
                notify_suffix = "（常に通知）"
            else:
                notify_suffix = f"（{notify_days_before}日前から通知）"
            if expiry_date:
                date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                message = f'"{item_name}" を期限 {date_text} で登録します{notify_suffix}。よろしいですか？'
            else:
                message = f'"{item_name}" を登録します{notify_suffix}。よろしいですか？'
        elif intent == "register_habit":
            DOW_NAMES = ["月", "火", "水", "木", "金", "土", "日"]
            if frequency == "weekly":
                dow = parsed.get("notify_day_of_week")
                day_text = f"毎週{DOW_NAMES[dow]}曜日" if dow is not None else "毎週"
            elif frequency == "monthly":
                dom = parsed.get("notify_day_of_month")
                day_text = f"毎月{dom}日" if dom is not None else "毎月"
            else:
                day_text = "毎日"
            time_text = notify_time or "12:00"
            message = f'習慣タスク "{item_name}" を登録します（{day_text} {time_text} にリマインド）。よろしいですか？'
        elif intent == "update_habit_frequency":
            DOW_NAMES = ["月", "火", "水", "木", "金", "土", "日"]
            dow = parsed.get("notify_day_of_week")
            dom = parsed.get("notify_day_of_month")
            if frequency == "weekly":
                label = f"毎週{DOW_NAMES[dow]}曜日" if dow is not None else "毎週"
            elif frequency == "monthly":
                label = f"毎月{dom}日" if dom is not None else "毎月"
            else:
                label = "毎日"
            message = f'習慣タスク "{item_name}" の頻度を {label} に変更します。よろしいですか？'
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
            label = "常に通知" if notify_days_before is None else f"{notify_days_before}日前から通知"
            message = f'"{item_name}" の通知を {label} に設定します。よろしいですか？'
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
                    notify_days_before=operation.get("notify_days_before"),
                )
            )
            if parsed_expiry_date:
                self._line_response_service.add_message(
                    f'"{item_name}" を期限{parsed_expiry_date.strftime("%Y年%m月%d日")}で登録しました。'
                )
                self._pending_operation_service.clear(line_user_id)
                self._pending_operation_service.save(
                    line_user_id,
                    {"intent": "update_recent_notify", "item_name": item_name},
                )
                return
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
                if filter_expiry or exclude_expiry:
                    remaining = self._stock_repository.find(
                        query={"owner_id": line_user_id, "item_name": item_name, "status": 1}
                    )
                    if remaining:
                        dates = [s.expiry_date.strftime("%Y/%m/%d") if s.expiry_date else "期限なし" for s in remaining]
                        self._line_response_service.add_message(
                            f'その条件に一致する "{item_name}" は見つかりませんでした。\n'
                            f'現在登録中: {", ".join(dates)}'
                        )
                    else:
                        self._line_response_service.add_message(
                            f'"{item_name}" は見つかりませんでした（削除済みか未登録）。'
                        )
                else:
                    self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            else:
                self._line_response_service.add_message(f'"{item_name}" を削除しました。')
        elif intent == "register_habit":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク登録は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            DOW_NAMES = ["月", "火", "水", "木", "金", "土", "日"]
            frequency = operation.get("frequency") or "daily"
            notify_time = operation.get("notify_time") or "12:00"
            self._habit_task_repository.create(
                HabitTask(
                    owner_id=line_user_id,
                    task_name=item_name,
                    frequency=frequency,
                    notify_time=notify_time,
                    notify_day_of_week=operation.get("notify_day_of_week"),
                    notify_day_of_month=operation.get("notify_day_of_month"),
                    is_active=True,
                )
            )
            if frequency == "weekly":
                dow = operation.get("notify_day_of_week")
                day_text = f"毎週{DOW_NAMES[dow]}曜日" if dow is not None else "毎週"
            elif frequency == "monthly":
                dom = operation.get("notify_day_of_month")
                day_text = f"毎月{dom}日" if dom is not None else "毎月"
            else:
                day_text = "毎日"
            self._line_response_service.add_message(
                f'習慣タスク "{item_name}" を登録しました（{day_text} {notify_time} にリマインド）。'
            )
        elif intent == "delete_habit":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク操作は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            count = self._habit_task_repository.update(
                query={"owner_id__in": self._get_habit_owner_ids(line_user_id), "task_name": item_name, "is_active": True},
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
                query={"owner_id__in": self._get_habit_owner_ids(line_user_id), "task_name": item_name, "is_active": True},
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
                new_values={"notify_days_before": operation.get("notify_days_before")},
            )
            if count > 0:
                self._line_response_service.add_message(f'"{item_name}" の通知設定を更新しました。')
            else:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
        elif intent == "update_habit_frequency":
            if self._habit_task_repository is None:
                self._line_response_service.add_message("習慣タスク操作は現在利用できません。")
                self._pending_operation_service.clear(line_user_id)
                return
            count = self._habit_task_repository.update(
                query={"owner_id__in": self._get_habit_owner_ids(line_user_id), "task_name": item_name, "is_active": True},
                new_values={
                    "frequency": operation.get("frequency") or "daily",
                    "notify_day_of_week": operation.get("notify_day_of_week"),
                    "notify_day_of_month": operation.get("notify_day_of_month"),
                },
            )
            if count > 0:
                self._line_response_service.add_message(f'習慣タスク "{item_name}" の頻度を変更しました。')
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
                {"owner_id__in": self._get_habit_owner_ids(line_user_id), "task_name": item_name, "is_active": True}
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
        if operation.get("intent") == "update_recent_notify":
            return self._handle_recent_notify_update(line_user_id, message, operation)

        if operation.get("intent") != "update_recent_expiry":
            return False

        item_name = operation.get("item_name")

        if message in ("なし", "不要", "いらない", "NO", "no"):
            self._pending_operation_service.clear(line_user_id)
            self._pending_operation_service.save(
                line_user_id,
                {"intent": "update_recent_notify", "item_name": item_name},
            )
            self._line_response_service.add_message("期限なしのままにしました。")
            return True

        parsed_date = self._parse_followup_expiry_date(message)
        if parsed_date is None:
            self._line_response_service.add_message(
                '期限を解釈できませんでした。「15日で」「明日で」「3/15で」のように送ってください。'
            )
            return True

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
        self._pending_operation_service.save(
            line_user_id,
            {"intent": "update_recent_notify", "item_name": item_name},
        )
        self._line_response_service.add_message(
            f'"{item_name}" の期限を{parsed_date.strftime("%Y年%m月%d日")}に更新しました。'
        )
        return True

    def _handle_recent_notify_update(self, line_user_id: str, message: str, operation: dict) -> bool:
        """直近登録アイテムへの通知設定フォローアップを処理する。"""
        item_name = operation.get("item_name")

        # アイテム名を補完してNLPに渡す（例: "確定申告の通知は3日前から"）
        parsed = self._intent_parser_service.parse(f"{item_name}の{message}")

        if parsed.get("intent") != "update_stock_notify":
            # 通知設定変更として解釈できない → コンテキスト破棄して通常処理へ
            self._pending_operation_service.clear(line_user_id)
            return False

        self._update_recent_item_notify(line_user_id, item_name, parsed.get("notify_days_before"))
        self._pending_operation_service.clear(line_user_id)
        return True

    def _update_recent_item_notify(self, line_user_id: str, item_name: str, notify_days_before) -> None:
        stocks = self._stock_repository.find(
            query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
            sort=[("created_at", "desc")],
        )
        if not stocks:
            self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            return
        self._stock_repository.update(
            query={"_id": stocks[0]._id},
            new_values={"notify_days_before": notify_days_before},
        )
        label = "常に通知" if notify_days_before is None else f"{notify_days_before}日前から通知"
        self._line_response_service.add_message(
            f'"{item_name}" の通知を{label}に設定しました。'
        )

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
