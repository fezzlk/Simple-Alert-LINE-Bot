from src import config
from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)
from src.Infrastructure.Repositories import line_user_repository, stock_repository


class CheckExpiredStockUseCase(IUseCase):
    def execute(self) -> None:
        line_users = line_user_repository.find()
        for line_user in line_users:
            # [TODO] LINE ユーザー取得時に関連する web ユーザー id もまとめて取得するようにする
            web_users = line_user_repository.find({
                '$and': [
                    {'linked_line_user_id': line_user.line_user_id},
                    {'is_linked_line_user': True},
                ],
            })
            web_user_id = '' if len(web_users) == 0 else web_users[0]._id
            stocks = stock_repository.find({
                '$or': [
                    {'owner_id': line_user.line_user_id},
                    {'owner_id': web_user_id},
                ],
            })
            messages = []
            print(stocks)
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
                messages.append(
                    '賞味期限が近づいている食材はありません。[TODO]このような場合は通知しないように設定できる')
            line_response_service.add_message('\n'.join(messages))
            line_response_service.add_message(
                f'webで確認する→ {config.SERVER_URL}/stock')

            line_response_service.push(to=line_user.line_user_id)
