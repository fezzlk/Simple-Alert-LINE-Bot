from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)


class ReplyStockUseCase(IUseCase):
    def execute() -> None:
        line_response_service.add_message('在庫一覧を表示')
