from linebot.v3.messaging import (
    TextMessage,
    TemplateMessage,
    ImageMessage,
    ButtonsTemplate,
    PushMessageRequest,
    ReplyMessageRequest,
)
from typing import List, Union
from src.line_bot_api import line_bot_api
from linebot.v3.webhooks import Event
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class LineResponseService(ILineResponseService):

    def __init__(self):
        self.texts: List[TextMessage] = []
        self.buttons: List[Union[TemplateMessage, ButtonsTemplate]] = []
        self.images: List[ImageMessage] = []

    def add_message(
        self,
        text: str,
    ) -> None:
        self.texts.append(TextMessage(text=text))

    def add_image(self, image_url: str) -> None:
        self.images.append(
            ImageMessage(
                original_content_url=image_url,
                preview_image_url=image_url,
            )
        )

    def reply(self, event: Event) -> None:
        contents = self.texts + self.buttons + self.images

        if (len(contents) == 0):
            return
        if hasattr(event, 'reply_token'):
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=contents,
                )
            )
        self.reset()

    def push(self, to: str) -> None:
        contents = self.texts + self.buttons + self.images
        if (len(contents) == 0):
            return
        line_bot_api.push_message(
            PushMessageRequest(
                to=to,
                messages=contents,
            )
        )
        self.reset()

    def reset(self) -> None:
        self.texts = []
        self.buttons = []
        self.images = []

    def push_a_message(self, to: str, message: str) -> None:
        line_bot_api.push_message(
            PushMessageRequest(
                to=to,
                messages=[TextMessage(text=message)],
            )
        )
