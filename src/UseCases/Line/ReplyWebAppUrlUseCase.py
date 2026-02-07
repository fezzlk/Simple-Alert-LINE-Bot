from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class ReplyWebAppUrlUseCase(IUseCase):
    def __init__(self, line_response_service: ILineResponseService):
        self._line_response_service = line_response_service

    def execute(self) -> None:
        self._line_response_service.add_message(
            f'{config.SERVER_URL}/stock?openExternalBrowser=1')
