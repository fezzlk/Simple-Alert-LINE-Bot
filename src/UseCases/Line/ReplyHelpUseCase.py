from typing import List
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
        messages = get_description(keyword)
        for message in messages:
            line_response_service.add_message(message)


def get_description(keyword) -> List[str]:
    if keyword is None:
        use_case_list = get_line_command_use_case_list()
        commands = '\n'.join(['\n'.join(v)
                              for _, v in use_case_list.items()])
        return [
            '使用可能なコマンド一覧を表示します',
            commands,
            '"ヘルプ [コマンド名]"\nで詳細が見れます',
        ]
    elif keyword == '遅延':
        return ['京浜東北線と横須賀線の運行情報を表示します']
    elif keyword == '天気':
        return ['横浜の天気を表示します']
    elif keyword == 'ストック一覧':
        return [
            '登録したストックを一覧で表示します',
            '新規登録する場合は\n"ストック登録 [アイテム名] [期限(任意)]"\nと送ってください。',
        ]
    elif keyword == 'ストック登録':
        return [
            '食材やポイントカードなどの期限を管理できます',
            '期限が近づいている場合、毎日12時に通知がきます',
            '"ストック登録 [アイテム名] [期限(任意)]"\nと送ってください。',
        ]
    elif keyword == 'ユーザー連携':
        return [
            'Web 上のアカウントと LINE アカウントを紐付けます',
            '紐付けが完了すると LINE で登録したストックを Web 上で確認できるようになります',
            f'まずは web 上でログインしてください → {config.SERVER_URL}/stock?openExternalBrowser=1',
            '次にこのチャットにて\n"ユーザー連携 [メールアドレス]"\nと送ってください。',
        ]
    elif keyword == 'URL':
        return [
            'Web アプリの URL を表示します',
        ]
    else:
        return ['このコマンドはまだ未完成なので決して使用してはいけません!']
