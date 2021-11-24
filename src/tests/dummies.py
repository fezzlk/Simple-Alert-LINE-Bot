from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.User import User


class IEvent(metaclass=ABCMeta):
    @abstractmethod
    def __init__(
        self,
        event_type: str,
        source_type: str,
        user_id: str,
        group_id: str,
        message_type: str,
        text: str,
        postback_data: str,
        mode: str,
    ):
        pass


class IProfile(metaclass=ABCMeta):
    @abstractmethod
    def __init__(
        self,
        display_name: str,
        user_id: str,
    ):
        pass


'''
    list 内の既存のインスタンスは変更禁止、追加のみ可能
    使用側では find_all などの特殊な場合を除いて [:3] などを使い追加に影響しないようにする
'''


def generate_dummy_user_list() -> List[User]:
    return [
        User(
            user_name='dummy_user_1',
            line_user_name='dummy_line_user_1',
            line_user_id='U0123456789abcdefghijklmnopqrstu1',
        ),
        User(
            user_name='dummy_user_2',
            line_user_name='dummy_line_user_2',
            line_user_id='U0123456789abcdefghijklmnopqrstu2',
        ),
        User(
            user_name='dummy_user_3',
            line_user_name='dummy_line_user_3',
            line_user_id='U0123456789abcdefghijklmnopqrstu3',
        ),
    ]


def generate_dummy_stock_list() -> List[Stock]:
    return [
        Stock(
            goods_name='dummy_good_1',
            owner_line_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=None,
            status=1,
        ),
        Stock(
            goods_name='dummy_good_2',
            owner_line_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=datetime(2020, 1, 1),
            status=1,
        ),
        Stock(
            goods_name='dummy_good_3',
            owner_line_id='U0123456789abcdefghijklmnopqrstu2',
            expiry_date=datetime(2020, 1, 1),
            status=1,
        ),
    ]


def generate_dummy_follow_event() -> IEvent:
    return Event(
        event_type='follow',
        source_type='user',
        user_id=generate_dummy_user_list()[0].line_user_id,
    )


def generate_dummy_unfollow_event() -> IEvent:
    return Event(
        event_type='unfollow',
        source_type='user',
        user_id=generate_dummy_user_list()[0].line_user_id,
    )


def generate_dummy_join_event() -> IEvent:
    return Event(
        event_type='join',
        source_type='group',
        user_id=generate_dummy_user_list()[0].line_user_id,
        group_id='dummy_line_group_id',
    )


def generate_dummy_text_message_event_from_user() -> IEvent:
    return Event(
        event_type='message',
        source_type='user',
        user_id=generate_dummy_user_list()[0].line_user_id,
        message_type='text',
        text='dummy_text',
    )


def generate_dummy_text_message_event_from_group() -> IEvent:
    return Event(
        event_type='message',
        source_type='group',
        user_id=generate_dummy_user_list()[0].line_user_id,
        group_id='dummy_line_group_id',
        message_type='text',
        text='dummy_text',
    )


def generate_dummy_profile() -> IProfile:
    return Profile(
        display_name='dummy_display_name',
        user_id='dummy_user_id',
    )


# LINE messaging API に合わせるためフィールド名はキャメルケースにしている
class Profile(IProfile):
    def __init__(
        self,
        display_name='dummy_display_name',
        user_id='dummy_user_id'
    ):
        self.display_name = display_name
        self.user_id = user_id


class Event(IEvent):
    def __init__(
        self,
        event_type='message',
        source_type='user',
        user_id=generate_dummy_user_list()[0].line_user_id,
        group_id='dummy_line_group_id',
        message_type='text',
        text='dummy_text',
        postback_data='dummy_postback_data',
        mode='active',
    ):
        self.type = event_type
        self.replyToken = 'dummy_reply_token'
        self.source = Source(
            user_id=user_id,
            source_type=source_type,
            group_id=group_id)
        self.mode = mode
        if self.type == 'message':
            self.message = Message(text=text, message_type=message_type)
        if self.type == 'postback':
            self.postback == Postback(data=postback_data)


class Source:
    def __init__(
        self,
        user_id=generate_dummy_user_list()[0].line_user_id,
        source_type='user',
        group_id='dummy_line_group_id',
    ):
        self.type = source_type
        self.user_id = user_id

        if source_type == 'group':
            self.group_id = group_id


class Message:
    def __init__(self, text='dummy_text', message_type='text'):
        self.type = message_type
        self.id = 'dummy_message_id'

        if message_type == 'image':
            self.contentProvider = {'type': 'line'}
        elif message_type == 'text':
            self.text = text


class Postback:
    def __init__(self, data=''):
        self.data = data
