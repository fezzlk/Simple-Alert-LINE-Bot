from src import config
from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class CheckExpiredStockUseCase(IUseCase):
    def __init__(
        self,
        line_user_repository: ILineUserRepository,
        stock_repository: IStockRepository,
        line_response_service: ILineResponseService,
    ):
        self._line_user_repository = line_user_repository
        self._stock_repository = stock_repository
        self._line_response_service = line_response_service

    def execute(self) -> None:
        line_users = self._line_user_repository.find()
        for line_user in line_users:
            print('# line_user_name')
            print(line_user.line_user_name)
            # [TODO] LINE アカウント取得時に関連する web ユーザー id もまとめて取得するようにする
            web_users = self._line_user_repository.find({
                '$and': [
                    {'linked_line_user_id': line_user.line_user_id},
                    {'is_linked_line_user': True},
                ],
            })
            web_user_id = '' if len(web_users) == 0 else web_users[0]._id
            print('# web_user_id')
            print(web_user_id)
            stocks = self._stock_repository.find({
                '$and': [
                    {'$or': [
                        {'owner_id': line_user.line_user_id},
                        {'owner_id': web_user_id},
                    ]},
                    {'status': 1},
                ],
            })

            expired_stocks = []
            stocks_with_expire_date = []
            stocks_without_expire_date = []
            for stock in stocks:

                print('# stock')
                print(stock.item_name)

                print('# expiry_date')
                print(stock.expiry_date)

                if stock.expiry_date is None:
                    elapsed_time = (datetime.now() - stock.created_at).days + 1
                    stocks_without_expire_date.append(
                        f'{stock.item_name}: 登録から{elapsed_time}日目')
                    continue

                days_until_expire = (
                    stock.expiry_date - datetime.now()
                ).days + 1

                print('# days_until_expire')
                print(days_until_expire)
                if days_until_expire < 0:
                    print('# 期限切れ')
                    expired_stocks.append(
                        f'{stock.item_name}: x ({days_until_expire * -1}日超過)')
                elif days_until_expire == 0:
                    print('# 当日')
                    stocks_with_expire_date.append(
                        f'{stock.item_name}: 今日まで')
                elif days_until_expire < 7:
                    print('# 期限内')
                    stocks_with_expire_date.append(
                        f'{stock.item_name}: あと{days_until_expire}日')

            messages = expired_stocks\
                + stocks_with_expire_date\
                + stocks_without_expire_date
            if len(messages) == 0:
                messages.append(
                    '期限が近づいているストックはありません。[TODO]このような場合は通知しないように設定できる')

            self._line_response_service.add_message('\n'.join(messages))
            self._line_response_service.add_message(
                f'webで確認する→ {config.SERVER_URL}/stock?openExternalBrowser=1')

            self._line_response_service.push(to=line_user.line_user_id)
