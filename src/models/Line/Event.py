from dataclasses import dataclass
from .Source import Source
from .Message import Message
from .Postback import Postback


@dataclass()
class Event:
    event_type: str
    event_list = ['follow', 'unfollow', 'message']  # TODO 要調査

    message_type: str
    text: str
    postback_data: str
    mode: str
    reply_token: str
    postback: Postback
    source: Source

    def __init__(
        self,
        event_type='message',
        source_type='user',
        user_id='',
        group_id='',
        message_type='text',
        text='dummy_text',
        postback_data='dummy_postback_data',
        mode='active',
    ):
        if event_type in self.event_list:
            self.event_type = event_type
        else:
            raise ValueError(
                f'{event_type} is invalid as "event_type" of Event')

        self.source = Source(
            user_id=user_id,
            source_type=source_type,
            group_id=group_id)

        self.mode = mode

        if self.event_type == 'follow':
            self.reply_token = 'dummy_reply_token'
        if self.event_type == 'message':
            self.reply_token = 'dummy_reply_token'
            self.message = Message(text=text, message_type=message_type)
        if self.event_type == 'postback':
            self.reply_token = 'dummy_reply_token'
            self.postback == Postback(data=postback_data)
