from src.services import (
    line_response_service,
)


class JoinUseCase:
    def execute(self) -> None:
        line_response_service.add_message('現在はテキストメッセージのみ対応しています。')
