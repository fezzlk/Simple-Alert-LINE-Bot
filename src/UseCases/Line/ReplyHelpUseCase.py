from linebot.models import MessageAction, QuickReply, QuickReplyButton, TextSendMessage

from src import config
from src.UseCases.Interface.IUseCase import IUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService

_QUICK_REPLY_BUTTONS = QuickReply(items=[
    QuickReplyButton(action=MessageAction(label='➕ 登録の使い方', text='使い方 登録')),
    QuickReplyButton(action=MessageAction(label='📄 一覧の使い方', text='使い方 一覧')),
    QuickReplyButton(action=MessageAction(label='🔗 連携の使い方', text='使い方 アカウント連携')),
])


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
        text = self._get_description(keyword)

        if keyword is None and hasattr(self._line_response_service, 'buttons'):
            self._line_response_service.buttons.append(
                TextSendMessage(text=text, quick_reply=_QUICK_REPLY_BUTTONS)
            )
        else:
            self._line_response_service.add_message(text)

    def _get_description(self, keyword) -> str:
        if keyword is None:
            return (
                '📋 Simple Alert の使い方\n\n'
                'このBotでできること：\n'
                '• 期限・締切のあるものを登録して通知を受け取る\n'
                '• 期限1週間前から毎日12時にリマインド\n'
                '• 習慣タスクの記録・管理\n\n'
                '💬 使い方はシンプル。やりたいことを日本語で送るだけ！\n\n'
                '【登録】\n「卵 3/15まで」「ライブチケット 3/20まで」\n\n'
                '【更新】\n「卵の期限を3/22にして」\n\n'
                '【削除】\n「卵を使い切った」\n\n'
                '【一覧確認】\n「一覧」と送るか、下のメニューから'
            )
        elif keyword in ('一覧', '一覧表示', 'リスト表示'):
            return (
                '📄 一覧表示\n\n'
                '登録中のアイテムをすべて表示します。\n\n'
                '「一覧」と送るか、メニューの「一覧」ボタンを押してください。\n'
                'Web画面で確認したい場合はメニューの「Web一覧」から。'
            )
        elif keyword in ('登録', '追加'):
            return (
                '➕ アイテムの登録\n\n'
                '登録できるもの：食材・日用品・チケット・締切タスクなど\n\n'
                '【送り方の例】\n'
                '「卵 3/15まで」\n'
                '「ライブチケット購入 3/20まで」\n'
                '「レポート提出 2/28まで」\n\n'
                '期限1週間前から毎日12時に通知が届きます。\n\n'
                '更新：「卵の期限を3/22にして」\n'
                '削除：「卵を使い切った」'
            )
        elif keyword == 'アカウント連携':
            return (
                '✅ ログインについて\n\n'
                'アカウント連携機能は廃止されました。\n\n'
                '現在はLINEアカウントで直接ログインできます。\n'
                f'こちらからWebアプリにアクセスしてください👇\n'
                f'{config.SERVER_URL}/stock?openExternalBrowser=1'
            )
        elif keyword in ('URL', 'web', 'Web'):
            return 'WebアプリのURLを表示します。'
        else:
            return (
                '📋 Simple Alert の使い方\n\n'
                'やりたいことを日本語で送るだけで操作できます。\n\n'
                '「卵 3/15まで」→ 登録\n'
                '「卵の期限を3/22にして」→ 更新\n'
                '「卵を使い切った」→ 削除\n'
                '「一覧」→ 一覧表示'
            )
