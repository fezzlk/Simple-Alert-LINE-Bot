from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)
from src.Infrastructure.Repositories import line_user_repository, stock_repository


class CheckExpiredStockUseCase(IUseCase):
    def execute(self) -> None:
        line_users = line_user_repository.find()
        for user in line_users:
            stocks = stock_repository.find(
                {'owner_id': user.line_user_id}
            )
            messages = []
            for stock in stocks:
                if stock.expiry_date is None:
                    continue
                days_until_expire = (
                    stock.expiry_date - datetime.now()
                ).days
                print(days_until_expire)
                if days_until_expire < 0:
                    messages.append(
                        f'{stock.item_name}: x ({days_until_expire * -1}日超過)')
                elif days_until_expire == 0:
                    messages.append(
                        f'{stock.item_name}: 今日まで')
                elif days_until_expire < 7:
                    messages.append(
                        f'{stock.item_name}: あと{days_until_expire}日')
            if len(messages) == 0:
                messages[0] = '賞味期限が近づいている食材はありません。'
            line_response_service.add_message('\n'.join(messages))
            line_response_service.push(to=user.line_user_id)
