from src.services import line_request_service, line_response_service
from src.Infrastructure.Repositories import web_user_repository
from src.UseCases.Interface.IUseCase import IUseCase


class RequestLinkLineWebUseCase(IUseCase):
    def execute(self) -> None:
        args = line_request_service.message.split()

        if len(args) != 2:
            line_response_service.add_message(
                'Web アカウントと紐付けするには "ユーザー連携 [メールアドレス]" と送ってください。')
            return

        email = args[1]
        web_users = web_user_repository.find({'web_user_email': email})

        if len(web_users) == 0:
            # URLも送るようにする
            line_response_service.add_message(
                f'{email} は登録されていません。一度ブラウザでログインしてください。')
            return

        if web_users[0].is_linked_line_user:
            # 紐付け中 LINE アカウント確認画面のURLも送るようにする
            line_response_service.add_message(
                f'{email} はすでにLINEアカウントと紐付けされています。')
            return

        result = web_user_repository.update(
            {'_id': web_users[0]._id},
            {'linked_line_user_id': line_request_service.req_line_user_id},
        )

        if result == 0:
            line_response_service.add_message('ユーザー連携リクエストに失敗しました。')
            return

        line_response_service.add_message(
            'ユーザー連携リクエストを送信しました。ブラウザでログインし、承認してください。')
