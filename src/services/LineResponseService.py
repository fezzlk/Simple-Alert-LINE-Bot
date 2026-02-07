from linebot.models import (
    TextSendMessage,
    TemplateSendMessage,
    ImageSendMessage,
    ButtonsTemplate,
)
from typing import List
from ctypes import Union
from src.line_bot_api import line_bot_api
from linebot.models.events import Event
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class LineResponseService(ILineResponseService):

    def __init__(self):
        self.texts: List[TextSendMessage] = []
        self.buttons: List[Union[TemplateSendMessage, ButtonsTemplate]] = []
        self.images: List[ImageSendMessage] = []

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

    def push(self, to: str) -> None:
        contents = self.texts + self.buttons + self.images
        if (len(contents) == 0):
            return
        line_bot_api.push_message(to, contents)
        self.reset()

    def reset(self) -> None:
        self.texts = []
        self.buttons = []
        self.images = []

    def push_a_message(self, to: str, message: str) -> None:
        line_bot_api.push_message(to, [TextSendMessage(text=message)])
