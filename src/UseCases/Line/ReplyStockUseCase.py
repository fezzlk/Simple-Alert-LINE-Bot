from src import config
from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.Infrastructure.Repositories import stock_repository, web_user_repository


class ReplyStockUseCase(IUseCase):
    def execute(self) -> None:
        linked_web_users = web_user_repository.find({
            'linked_line_user_id': line_request_service.req_line_user_id,
            'is_linked_line': True,
        })
        linked_web_user_id = linked_web_users[0]._id if len(
            linked_web_users) != 0 else ''
        stocks = stock_repository.find({
            '$and': [
                {'$or': [
                    {'owner_id': linked_web_user_id},
                    {'owner_id': line_request_service.req_line_user_id},
                ]},
                {'status': 1},
            ],
        })
        messages = []
        for stock in stocks:
            if stock.expiry_date is not None:
                messages.append(
                    f'{stock.item_name}: {stock.expiry_date.date()}')
            else:
                elapsed_time = (datetime.now() - stock.created_at).days
                messages.append(f'{stock.item_name}: 登録から{elapsed_time}日')

        line_response_service.add_message('\n'.join(messages))
        line_response_service.add_message(
            f'webで確認する→ {config.SERVER_URL}/stock?openExternalBrowser=1')
