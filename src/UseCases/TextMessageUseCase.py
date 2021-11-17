from src.services import (
    line_response_service,
)


class TextMessageUseCase:
    def execute(self) -> None:
        line_response_service.add_message('テキストメッセージを受け取りました。')
