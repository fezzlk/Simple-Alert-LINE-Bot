from datetime import datetime
from typing import List
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.LineUser import LineUser
from src.Domains.Entities.WebUser import WebUser
from dataclasses import dataclass


# LINE messaging API に合わせるためフィールド名はキャメルケースにしている
@dataclass()
class Profile:
    def __init__(
        self,
        display_name='dummy_display_name',
        user_id='dummy_line_user_id'
    ):
        self.display_name = display_name
        self.user_id = user_id


@dataclass()
class Event:
    def __init__(
        self,
        type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        group_id='dummy_line_group_id',
        message_type='text',
        text='dummy_text',
        postback_data='dummy_postback_data',
        mode='active',
    ):
        self.type = type
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


@dataclass()
class Source:
    def __init__(
        self,
        user_id='U0123456789abcdefghijklmnopqrstu1',
        source_type='user',
        group_id='dummy_line_group_id',
    ):
        self.type = source_type
        self.user_id = user_id

        if source_type == 'group':
            self.group_id = group_id


@dataclass()
class Message:
    def __init__(self, text='dummy_text', message_type='text'):
        self.type = message_type
        self.id = 'dummy_message_id'

        if message_type == 'image':
            self.contentProvider = {'type': 'line'}
        elif message_type == 'text':
            self.text = text


@dataclass()
class Postback:
    def __init__(self, data=''):
        self.data = data


'''
    list 内の既存のインスタンスは変更禁止、追加のみ可能
    使用側では find_all などの特殊な場合を除いて [:3] などを使い追加に影響しないようにする
'''


def generate_dummy_line_user_list() -> List[LineUser]:
    return [
        LineUser(
            line_user_name='dummy_line_user_1',
            line_user_id='U0123456789abcdefghijklmnopqrstu1',
        ),
        LineUser(
            line_user_name='dummy_line_user_2',
            line_user_id='U0123456789abcdefghijklmnopqrstu2',
        ),
        LineUser(
            line_user_name='dummy_line_user_3',
            line_user_id='U0123456789abcdefghijklmnopqrstu3',
        ),
        LineUser(
            line_user_name='dummy_line_user_4',
            line_user_id='U0123456789abcdefghijklmnopqrstu4',
        ),
        LineUser(
            line_user_name='dummy_line_user_5',
            line_user_id='U0123456789abcdefghijklmnopqrstu5',
        ),
    ]


def generate_dummy_web_user_list() -> List[WebUser]:
    return [
        WebUser(
            web_user_name='dummy_web_user_1',
            web_user_email='dummy1@example.com',
        ),
        WebUser(
            web_user_name='dummy_web_user_2',
            web_user_email='dummy2@example.com',
        ),
        WebUser(
            web_user_name='dummy_web_user_3',
            web_user_email='dummy3@example.com',
        ),
        WebUser(
            web_user_name='dummy_web_user_4',
            web_user_email='dummy4@example.com',
            linked_line_user_id='U0123456789abcdefghijklmnopqrstu4',
        ),
        WebUser(
            web_user_name='dummy_web_user_5',
            web_user_email='dummy5@example.com',
            linked_line_user_id='U0123456789abcdefghijklmnopqrstu5',
            is_linked_line_user=True,
        ),
    ]


def generate_dummy_stock_list() -> List[Stock]:
    return [
        Stock(
            item_name='dummy_good_1',
            owner_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=None,
            status=1,
        ),
        Stock(
            item_name='dummy_good_2',
            owner_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=datetime(2020, 1, 1),
            status=1,
        ),
        Stock(
            item_name='dummy_good_3',
            owner_id='U0123456789abcdefghijklmnopqrstu2',
            expiry_date=datetime(2020, 1, 1),
            status=1,
        ),
    ]


def generate_dummy_follow_event() -> Event:
    return Event(
        type='follow',
        source_type='user',
        user_id=generate_dummy_line_user_list()[0].line_user_id,
    )


def generate_dummy_unfollow_event() -> Event:
    return Event(
        type='unfollow',
        source_type='user',
        user_id=generate_dummy_line_user_list()[0].line_user_id,
    )


def generate_dummy_join_event() -> Event:
    return Event(
        type='join',
        source_type='group',
        user_id=generate_dummy_line_user_list()[0].line_user_id,
        group_id='dummy_line_group_id',
    )


def generate_dummy_text_message_event_from_user() -> Event:
    return Event(
        type='message',
        source_type='user',
        user_id=generate_dummy_line_user_list()[0].line_user_id,
        message_type='text',
        text='dummy_text',
    )


def generate_dummy_text_message_event_from_group() -> Event:
    return Event(
        type='message',
        source_type='group',
        user_id=generate_dummy_line_user_list()[0].line_user_id,
        group_id='dummy_line_group_id',
        message_type='text',
        text='dummy_text',
    )


def generate_dummy_profile() -> Profile:
    return Profile(
        display_name='dummy_display_name',
        user_id='dummy_line_user_id',
    )
