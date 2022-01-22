from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)


class TextMessageUseCase(IUseCase):
    def execute(self) -> None:
        line_response_service.add_message('使い方がわからない場合は「ヘルプ」と送ってください')
