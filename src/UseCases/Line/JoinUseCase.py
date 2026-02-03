from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class JoinUseCase(IUseCase):
    def __init__(self, line_response_service: ILineResponseService):
        self._line_response_service = line_response_service

    def execute(self) -> None:
        self._line_response_service.add_message(
            '現在はテキストメッセージのみ対応しています。'
        )
