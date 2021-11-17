from src.services import (
    line_response_service,
)


class ReplyStockUseCase:
    def execute() -> None:
        line_response_service.add_message('在庫一覧を表示')
