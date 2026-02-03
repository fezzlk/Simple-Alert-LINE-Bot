from src import config
from bson.objectid import ObjectId
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
        args = self._line_request_service.message.split()

        if len(args) != 2:
            self._line_response_service.add_message(
                'Web アカウントと紐付けするには "アカウント連携 [メールアドレス]" と送ってください。')
            return

        email = args[1]
        web_users = self._web_user_repository.find({'web_user_email': email})

        if len(web_users) == 0:
            self._line_response_service.add_message(
                f'{email} は登録されていません。一度ブラウザでログインしてください。')
            self._line_response_service.add_message(
                f'{config.SERVER_URL}/line/approve?openExternalBrowser=1')
            return

        if web_users[0].is_linked_line_user:
            self._line_response_service.add_message(
                f'{email} はすでに LINE アカウントと紐付けされています。')
            self._line_response_service.add_message(
                f'{config.SERVER_URL}/line/approve?openExternalBrowser=1')
            return

        result = self._web_user_repository.update(
            {'_id': ObjectId(web_users[0]._id)},
            {'linked_line_user_id': self._line_request_service.req_line_user_id},
        )

        if result == 0:
            self._line_response_service.add_message('アカウント連携リクエストに失敗しました。')
            return

        self._line_response_service.add_message(
            'アカウント連携リクエストを送信しました。ブラウザでログインし、承認してください。')
        self._line_response_service.add_message(
            f'{config.SERVER_URL}/line/approve?openExternalBrowser=1')
