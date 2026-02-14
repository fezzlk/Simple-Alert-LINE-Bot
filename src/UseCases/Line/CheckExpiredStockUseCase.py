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
            web_users = self._line_user_repository.find({
                'linked_line_user_id': line_user.line_user_id,
                'is_linked_line_user': True,
            })
            web_user_id = '' if len(web_users) == 0 else web_users[0]._id
            stocks = self._stock_repository.find({
                'owner_id__in': [line_user.line_user_id, web_user_id],
                'status': 1,
            })
            if len(stocks) == 0:
                continue

            near_due_stocks = []
            today = datetime.now().date()
            for stock in stocks:
                if stock.expiry_date is None:
                    continue

                days_until_expire = (stock.expiry_date.date() - today).days
                if days_until_expire < 0 or days_until_expire > 3:
                    continue

                if days_until_expire == 0:
                    label = '今日まで'
                elif days_until_expire == 1:
                    label = '明日まで'
                else:
                    label = f'あと{days_until_expire}日'
                near_due_stocks.append(f'{stock.item_name}: {label}')

            self._line_response_service.add_message(
                f'今日の確認です。webで一覧を確認してください→ {config.SERVER_URL}/stock?openExternalBrowser=1'
            )

            if len(near_due_stocks) != 0:
                self._line_response_service.add_message(
                    '期限が3日以内のもの:\n' + '\n'.join(near_due_stocks)
                )

            self._line_response_service.push(to=line_user.line_user_id)
