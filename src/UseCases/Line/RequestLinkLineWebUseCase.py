from src import config
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class RequestLinkLineWebUseCase(IUseCase):
    def __init__(
        self,
        web_user_repository: IWebUserRepository,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
    ):
        self._web_user_repository = web_user_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service

    def execute(self) -> None:
        self._line_response_service.add_message(
            'アカウント連携機能は廃止されました。\n\n'
            '現在はLINEアカウントで直接ログインできます。\n'
            f'こちらからWebアプリにアクセスしてください👇\n'
            f'{config.SERVER_URL}/stock?openExternalBrowser=1'
        )
