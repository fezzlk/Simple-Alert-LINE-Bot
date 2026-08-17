from datetime import date, timedelta

from src import config
from src.services.HabitCalendarTokenService import generate_token
from src.UseCases.Interface.IUseCase import IUseCase


class SendWeeklyHabitCalendarUseCase(IUseCase):
    """直近7日間（昨日まで）の習慣タスク実績カレンダー画像をLINEで週次配信する。

    画像自体はここでは生成せず、署名付きトークンを埋め込んだ画像URLを
    ImageSendMessage として push する。実際の画像レンダリングは
    /_api/v1/habit_calendar/<token>.png がリクエストを受けた時点で行う
    （常時ストレージを持たず、都度オンザフライで描画する）。
    """

    def __init__(
        self,
        line_user_repository,
        web_user_repository,
        habit_task_repository,
        line_response_service,
    ):
        self._line_user_repository = line_user_repository
        self._web_user_repository = web_user_repository
        self._habit_task_repository = habit_task_repository
        self._line_response_service = line_response_service

    def execute(self) -> None:
        today = date.today()
        week_end = today - timedelta(days=1)
        week_start = week_end - timedelta(days=6)
        week_start_date = week_start.strftime("%Y-%m-%d")

        line_users = self._line_user_repository.find()
        for line_user in line_users:
            web_users = self._web_user_repository.find(
                {
                    "linked_line_user_id": line_user.line_user_id,
                    "is_linked_line_user": True,
                }
            )
            linked_web_user_id = web_users[0]._id if len(web_users) != 0 else ""

            tasks = self._habit_task_repository.find(
                {
                    "owner_id__in": [line_user.line_user_id, linked_web_user_id],
                    "is_active": True,
                }
            )
            if len(tasks) == 0:
                continue

            token = generate_token(
                line_user_id=line_user.line_user_id,
                week_start_date=week_start_date,
            )
            image_url = f'{config.SERVER_URL}/_api/v1/habit_calendar/{token}.png'
            self._line_response_service.add_image(image_url)
            self._line_response_service.push(to=line_user.line_user_id)
