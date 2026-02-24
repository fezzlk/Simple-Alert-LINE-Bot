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
        notification_schedule_repository=None,
    ):
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._line_user_service = line_user_service
        self._notification_schedule_repository = notification_schedule_repository

    def execute(self) -> None:
        name = self._line_request_service.req_line_user_name
        new_line_user = LineUser(
            line_user_name=name,
            line_user_id=self._line_request_service.req_line_user_id,
        )
        self._line_user_service.find_or_create(new_line_user=new_line_user)
        if self._notification_schedule_repository is not None:
            self._notification_schedule_repository.upsert(
                line_user_id=new_line_user.line_user_id,
                notify_time="12:00",
                timezone_name="Asia/Tokyo",
            )
        self._line_response_service.add_message(
            f"{name}さん、友達登録ありがとうございます！"
        )
        self._line_response_service.add_message(
            "ものやタスクの期限を通知、一覧管理します。"
        )
        self._line_response_service.add_message(
            "以下のように送信してください。\n\n・卵は3/15まで\n・ライブチケット購入 3/20まで\n・打ち合わせ日程調整 2/28まで"
        )
        self._line_response_service.add_message(
            "「一覧表示」「リスト表示」で一覧を表示します"
        )
        self._line_response_service.add_message(
            f"web サイトにログイン→ {config.SERVER_URL}/stock?openExternalBrowser=1"
        )
