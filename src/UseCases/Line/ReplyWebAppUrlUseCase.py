from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.line_rich_messages import add_stock_web_link_button


class ReplyWebAppUrlUseCase(IUseCase):
    def __init__(self, line_response_service: ILineResponseService):
        self._line_response_service = line_response_service

    def execute(self) -> None:
        add_stock_web_link_button(
            line_response_service=self._line_response_service,
            server_url=config.SERVER_URL,
        )
