from datetime import datetime, timezone

from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Interface.IUseCase import IUseCase


def _should_notify(stock, days_until_expire: int) -> bool:
    """notify_days_beforeに基づいて通知すべきかを判定"""
    if stock.notify_days_before is None:  # 常に通知
        return True
    return days_until_expire <= stock.notify_days_before


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
            notify_stocks = []
            for stock in stocks:
                if stock.expiry_date is None:
                    continue

                days_until_expire = (stock.expiry_date.date() - today).days

                if not _should_notify(stock, days_until_expire):
                    continue

                if days_until_expire < 0:
                    label = f"{abs(days_until_expire)}日超過"
                    icon = "🔴"
                elif days_until_expire == 0:
                    label = "今日まで"
                    icon = "🟠"
                elif days_until_expire == 1:
                    label = "明日まで"
                    icon = "🟠"
                elif days_until_expire <= 3:
                    label = f"残り{days_until_expire}日"
                    icon = "🟠"
                elif days_until_expire <= 7:
                    label = f"残り{days_until_expire}日"
                    icon = "🟡"
                else:
                    label = f"残り{days_until_expire}日"
                    icon = "🟢"
                notify_stocks.append(f"{icon} {stock.item_name}（{label}）")

            if not notify_stocks:
                continue

            self._line_response_service.add_message(
                f"📋 期限通知（{len(notify_stocks)}件）\n" + "\n".join(notify_stocks)
            )
            self._line_response_service.push(to=schedule.line_user_id)
