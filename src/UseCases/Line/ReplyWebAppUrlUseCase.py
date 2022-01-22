from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)


class ReplyWebAppUrlUseCase(IUseCase):
    def execute(self) -> None:
        line_response_service.add_message(
            f'{config.SERVER_URL}/stock?openExternalBrowser=1')
