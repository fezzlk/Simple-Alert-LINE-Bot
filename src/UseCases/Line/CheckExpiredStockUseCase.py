from datetime import datetime, timezone

from src import config
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Interface.IUseCase import IUseCase
from src.line_rich_messages import add_stock_web_link_button


class CheckExpiredStockUseCase(IUseCase):
    def __init__(
        self,
        notification_schedule_repository,
        web_user_repository: IWebUserRepository,
        stock_repository: IStockRepository,
        line_response_service: ILineResponseService,
    ):
        self._notification_schedule_repository = notification_schedule_repository
        self._web_user_repository = web_user_repository
        self._stock_repository = stock_repository
        self._line_response_service = line_response_service

    def execute(self) -> None:
        now_utc = datetime.now(timezone.utc)
        due_schedules = self._notification_schedule_repository.find_due(now_utc=now_utc)
        if len(due_schedules) == 0:
            return

        due_line_user_ids = [s.line_user_id for s in due_schedules]
        linked_web_users = self._web_user_repository.find(
            {
                "linked_line_user_id__in": due_line_user_ids,
                "is_linked_line_user": True,
            }
        )
        web_user_id_map = {user.linked_line_user_id: user._id for user in linked_web_users}
        today = datetime.now().date()

        for schedule in due_schedules:
            claimed = self._notification_schedule_repository.claim_and_schedule_next(
                line_user_id=schedule.line_user_id,
                now_utc=now_utc,
            )
            if not claimed:
                continue

            web_user_id = web_user_id_map.get(schedule.line_user_id, "")
            stocks = self._stock_repository.find(
                {
                    "owner_id__in": [schedule.line_user_id, web_user_id],
                    "status": 1,
                }
            )
            near_due_stocks = []
            notify_on_items = []
            for stock in stocks:
                if stock.notify_enabled:
                    notify_on_items.append(stock.item_name)

                if stock.expiry_date is None:
                    continue

                days_until_expire = (stock.expiry_date.date() - today).days
                if days_until_expire < 0 or days_until_expire > 3:
                    continue

                if days_until_expire == 0:
                    label = "今日まで"
                elif days_until_expire == 1:
                    label = "明日まで"
                else:
                    label = f"あと{days_until_expire}日"
                near_due_stocks.append(f"{stock.item_name}: {label}")

            if len(near_due_stocks) == 0:
                continue

            self._line_response_service.add_message(
                "期限が3日以内のもの:\n" + "\n".join(near_due_stocks)
            )
            add_stock_web_link_button(
                line_response_service=self._line_response_service,
                server_url=config.SERVER_URL,
            )
            if len(notify_on_items) == 0:
                self._line_response_service.add_message("通知ONのアイテム: なし")
            else:
                self._line_response_service.add_message(
                    "通知ONのアイテム:\n" + "\n".join(notify_on_items)
                )
            self._line_response_service.push(to=schedule.line_user_id)
