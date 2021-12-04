from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)
from src.Infrastructure.Repositories import line_user_repository, stock_repository


class NotifyStockUseCase(IUseCase):
    def execute(self) -> None:
        line_users = line_user_repository.find()
        for user in line_users:
            stocks = stock_repository.find(
                {'owner_line_id': user.line_user_id})
            messages = []
            for stock in stocks:
                elapsed_time = (datetime.now() - stock.created_at).days
                messages.append(f'{stock.goods_name}: {elapsed_time}日経過')
            line_response_service.add_message('\n'.join(messages))
            line_response_service.push(to=user.line_user_id)
