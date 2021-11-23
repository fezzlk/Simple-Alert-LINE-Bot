from linebot.models import (
    TextSendMessage,
    TemplateSendMessage,
    ImageSendMessage,
    ButtonsTemplate,
    PostbackAction,
)

from src.line_bot_api import line_bot_api
from linebot.models.events import Event


class LineResponseService:

    def __init__(self):
        self.texts = []
        self.buttons = []
        self.images = []

    def add_message(
        self,
        text: str,
    ) -> None:
        self.texts.append(TextSendMessage(text=text))

    def add_image(self, image_url: str) -> None:
        self.images.append(
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url,
            )
        )

    def add_start_menu(self) -> None:
        self.buttons.append(
            TemplateSendMessage(
                alt_text='Start Menu',
                template=ButtonsTemplate(
                    title='スタートメニュー',
                    text='何をしますか？',
                    actions=[
                        PostbackAction(
                            label='天気を確認',
                            display_text='天気を確認',
                            data='_weather'
                        ),
                        PostbackAction(
                            label='遅延情報を確認',
                            display_text='遅延情報を確認',
                            data='_train'
                        ),
                        PostbackAction(
                            label='食材を確認',
                            display_text='食材を確認',
                            data='_stock'
                        ),
                    ]
                )
            )
        )

    def reply(self, event: Event) -> None:
        contents = self.texts + self.buttons + self.images

        if (len(contents) == 0):
            return
        if hasattr(event, 'reply_token'):
            line_bot_api.reply_message(
                event.reply_token,
                contents,
            )
        self.reset()

    def reset(self) -> None:
        self.texts = []
        self.buttons = []
        self.images = []
