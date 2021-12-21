from src import config
from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)
from src.Infrastructure.Repositories import stock_repository


class ReplyStockUseCase(IUseCase):
    def execute(self) -> None:
        stocks = stock_repository.find()
        line_response_service.add_message('食材と登録日からの日数を表示します。')
        messages = []
        for stock in stocks:
            elapsed_time = (datetime.now() - stock.created_at).days
            messages.append(f'{stock.item_name}: {elapsed_time}日')
        line_response_service.add_message('\n'.join(messages))
        line_response_service.add_message(
            f'webで確認する→ {config.SERVER_URL}/stock')
