from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.Entities.LineUser import LineUser
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Interface.ILineUserService import ILineUserService


class FollowUseCase(IUseCase):
    def __init__(
        self,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
        line_user_service: ILineUserService,
    ):
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._line_user_service = line_user_service

    def execute(self) -> None:
        name = self._line_request_service.req_line_user_name
        new_line_user = LineUser(
            line_user_name=name,
            line_user_id=self._line_request_service.req_line_user_id,
        )
        self._line_user_service.find_or_create(new_line_user=new_line_user)
        self._line_response_service.add_message(f'{name}さん、友達登録ありがとうございます！')
        self._line_response_service.add_message('「使い方」や「使い方教えて」でガイドを表示できます。')
        self._line_response_service.add_message(
            '使い方: 例) 「卵は3/15まで」「ライブチケット購入 3/20まで」「打ち合わせ日程調整 2/28まで」。'
        )
        self._line_response_service.add_message(
            '「一覧表示」「リスト表示」で一覧表示、「webで操作」「webで表示」でWebリンク表示。'
        )
        self._line_response_service.add_message(
            f'web で確認する→ {config.SERVER_URL}/stock?openExternalBrowser=1')
