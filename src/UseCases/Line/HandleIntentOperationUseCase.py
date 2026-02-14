from datetime import datetime, timedelta
import re

from linebot.models import ButtonsTemplate, PostbackAction, TemplateSendMessage

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
    ):
        self._stock_repository = stock_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._intent_parser_service = intent_parser_service
        self._pending_operation_service = pending_operation_service

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
            },
        )
        self._reply_confirmation(parsed)

    def _reply_confirmation(self, parsed):
        intent = parsed["intent"]
        item_name = parsed["item_name"]
        expiry_date = parsed["expiry_date"]

        if intent == "register":
            if expiry_date:
                date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                message = f'"{item_name}" を期限 {date_text} で登録します。よろしいですか？'
            else:
                message = f'"{item_name}" を登録します。よろしいですか？'
        elif intent == "update":
            date_text = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
            message = f'"{item_name}" の期限を {date_text} に更新します。よろしいですか？'
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
                    notify_enabled=False,
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
            count = self._stock_repository.update(
                query={"owner_id": line_user_id, "item_name": item_name, "status": 1},
                new_values={"status": 2},
            )
            if count == 0:
                self._line_response_service.add_message(f'"{item_name}" が見つかりませんでした。')
            else:
                self._line_response_service.add_message(f'"{item_name}" を削除しました。')
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
