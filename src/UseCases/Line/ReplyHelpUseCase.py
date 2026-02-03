from typing import List
from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class ReplyHelpUseCase(IUseCase):
    def __init__(
        self,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
        commands: List[str],
    ):
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service
        self._commands = commands

    def execute(self) -> None:
        args = self._line_request_service.message.split()
        keyword = args[1] if len(args) >= 2 else None
        messages = self._get_description(keyword)
        for message in messages:
            self._line_response_service.add_message(message)

    def _get_description(self, keyword) -> List[str]:
        if keyword is None:
            commands = '\n'.join(self._commands)
            return [
                '使用可能なコマンド一覧を表示します',
                commands,
                '"ヘルプ [コマンド名]"\nで詳細が見れます',
            ]
        elif keyword == '遅延':
            return ['京浜東北線と横須賀線の運行情報を表示します']
        elif keyword == '天気':
            return ['横浜の天気を表示します']
        elif keyword == '一覧':
            return [
                '登録したアイテムを一覧で表示します',
                '新規登録する場合は\n"登録 [アイテム名] [期限(任意)]"\nと送ってください。',
            ]
        elif keyword == '登録':
            return [
                '食材やポイントカードなどの期限を管理できます',
                '期限が1週間前までに近づいている場合、毎日12時に通知がきます',
                '"登録 [アイテム名] [期限(任意)]"\nと送ってください。',
                '[期限の入力方法]\n\nYYYY年MM月DD日\n→ YYYYMMDD\n\n20YY年MM月DD日\n→ YYMMDD\n\n今年MM月DD日\n→ MMDD\n\n今月DD日\n→ DD',
            ]
        elif keyword == 'アカウント連携':
            return [
                'Web 上のアカウントと LINE アカウントを紐付けます',
                '紐付けが完了すると LINE で登録したストックを Web 上で確認できるようになります',
                f'まずは web 上でログインしてください → {config.SERVER_URL}/stock?openExternalBrowser=1',
                '次にこのチャットにて\n"アカウント連携 [メールアドレス]"\nと送ってください。',
            ]
        elif keyword == 'URL':
            return [
                'Web アプリの URL を表示します',
            ]
        else:
            return ['このコマンドはまだ未完成なので決して使用してはいけません!']
