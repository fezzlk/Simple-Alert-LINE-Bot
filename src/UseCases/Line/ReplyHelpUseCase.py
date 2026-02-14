from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class ReplyHelpUseCase(IUseCase):
    def __init__(
        self,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
    ):
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service

    def execute(self) -> None:
        args = self._line_request_service.message.split()
        keyword = args[1] if len(args) >= 2 else None
        messages = self._get_description(keyword)
        for message in messages:
            self._line_response_service.add_message(message)

    def _get_description(self, keyword):
        if keyword is None:
            return [
                '使い方ガイドです',
                '例: 「ソファ組み立て」「ライブチケット購入 3/20まで」「打ち合わせ日程調整 2/28まで」',
                '「一覧表示」「リスト表示」で一覧、「webで操作」「webで表示」でWebリンクを返します',
                '更新例: 「卵の期限を3/22にして」 / 削除例: 「卵を使い切った」',
            ]
        elif keyword in ('一覧', '一覧表示', 'リスト表示'):
            return [
                '登録したアイテムを一覧で表示します',
                '例: 「一覧表示」または「登録済み一覧」',
            ]
        elif keyword in ('登録', '追加'):
            return [
                '食材・家具などの非食品・チケット購入・日程調整などを管理できます',
                '期限が1週間前までに近づいている場合、毎日12時に通知がきます',
                '例: 「卵は3/15まで」「ライブチケット購入 3/20まで」「打ち合わせ日程調整 2/28まで」',
                '更新は「卵の期限を3/22にして」、削除は「卵を使い切った」と送ってください。',
            ]
        elif keyword == 'アカウント連携':
            return [
                'Web 上のアカウントと LINE アカウントを紐付けます',
                '紐付けが完了すると LINE で登録したストックを Web 上で確認できるようになります',
                f'まずは web 上でログインしてください → {config.SERVER_URL}/stock?openExternalBrowser=1',
                '次にこのチャットにて\n"アカウント連携 [メールアドレス]"\nと送ってください。',
            ]
        elif keyword in ('URL', 'web', 'Web'):
            return [
                'Web アプリの URL を表示します',
            ]
        else:
            return [
                '使い方ガイドです',
                '登録はアイテム名をそのまま送信（例: 「卵は3/15まで」）',
                '一覧は「一覧表示」、Webは「webで操作」と送ってください。',
            ]
