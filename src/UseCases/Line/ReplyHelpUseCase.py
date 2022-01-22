from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.UseCases.get_line_command_use_case_list import get_line_command_use_case_list


class ReplyHelpUseCase(IUseCase):
    def execute(self) -> None:
        args = line_request_service.message.split()
        keyword = args[1] if len(args) >= 2 else None

        if keyword is None:
            use_case_list = get_line_command_use_case_list()
            commands = '\n'.join(['\n'.join(v)
                                 for _, v in use_case_list.items()])
            line_response_service.add_message('使用可能なコマンド一覧を表示します')
            line_response_service.add_message(commands)
            line_response_service.add_message('"ヘルプ [コマンド名]"\nで詳細が見れます')
        elif keyword == '遅延':
            line_response_service.add_message('京浜東北線と横須賀線の運行情報を表示します')
        elif keyword == '天気':
            line_response_service.add_message('横浜の天気を表示します')
        elif keyword == 'ストック一覧':
            line_response_service.add_message('登録したストックを一覧で表示します')
            line_response_service.add_message(
                '新規登録する場合は\n"ストック登録 [アイテム名] [期限(任意)]"\nと送ってください。')
        elif keyword == 'ストック登録':
            line_response_service.add_message('食材やポイントカードなどの期限を管理できます')
            line_response_service.add_message('期限が近づいている場合、毎日12時に通知がきます')
            line_response_service.add_message(
                '"ストック登録 [アイテム名] [期限(任意)]"\nと送ってください。')
        elif keyword == 'ユーザー連携':
            line_response_service.add_message('Web 上のアカウントと LINE アカウントを紐付けます')
            line_response_service.add_message(
                '紐付けが完了すると LINE で登録したストックを Web 上で確認できるようになります')
            line_response_service.add_message(
                f'まずは web 上でログインしてください → {config.SERVER_URL}/stock?openExternalBrowser=1')
            line_response_service.add_message(
                '次にこのチャットにて\n"ユーザー連携 [メールアドレス]"\nと送ってください。')
        else:
            line_response_service.add_message('このコマンドはまだ未完成なので決して使用してはいけません')
