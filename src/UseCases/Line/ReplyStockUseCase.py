from src import config
from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.line_rich_messages import add_stock_web_link_button


class ReplyStockUseCase(IUseCase):
    def __init__(
        self,
        stock_repository: IStockRepository,
        web_user_repository: IWebUserRepository,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
    ):
        self._stock_repository = stock_repository
        self._web_user_repository = web_user_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service

    def execute(self) -> None:
        linked_web_users = self._web_user_repository.find({
            'linked_line_user_id': self._line_request_service.req_line_user_id,
            'is_linked_line': True,
        })
        linked_web_user_id = linked_web_users[0]._id if len(
            linked_web_users) != 0 else ''
        stocks = self._stock_repository.find({
            'owner_id__in': [
                linked_web_user_id,
                self._line_request_service.req_line_user_id,
            ],
            'status': 1,
        })

        stocks_with_expire_date = []
        stocks_without_expire_date = []
        for stock in stocks:
            if stock.expiry_date is not None:
                stocks_with_expire_date.append(
                    f'{stock.item_name}: {stock.expiry_date.strftime("%Y年%m月%d日")}')
            else:
                elapsed_time = (datetime.now() - stock.created_at).days + 1
                stocks_without_expire_date.append(
                    f'{stock.item_name}: 登録から{elapsed_time}日目')

        sections = []
        if len(stocks_without_expire_date) != 0:
            sections.append('期限未設定:\n' + '\n'.join(stocks_without_expire_date))
        if len(stocks_with_expire_date) != 0:
            sections.append('期限あり:\n' + '\n'.join(stocks_with_expire_date))
        if len(sections) == 0:
            sections.append('登録中のアイテムはありません。')

        self._line_response_service.add_message('\n\n'.join(sections))
        add_stock_web_link_button(
            line_response_service=self._line_response_service,
            server_url=config.SERVER_URL,
        )
