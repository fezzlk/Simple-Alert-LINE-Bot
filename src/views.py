import traceback
from typing import Callable, Dict
from flask import request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from src import app
from src.UseCases.Interface.IUseCase import IUseCase
from src.line_bot_api import handler
from src.UseCases import (
    follow_use_case,
    unfollow_use_case,
    postback_use_case,
    join_use_case,
    text_message_use_case,
    image_message_use_case,
    reply_train_delay_use_case,
    reply_weather_use_case,
    register_stock_use_case,
    reply_stock_use_case,
)
from linebot.models import (
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    MessageEvent,
    TextMessage,
    ImageMessage,
    PostbackEvent,
)
from src.services import line_request_service, line_response_service

'''
Endpoints for Web
'''


@app.route('/', methods=['GET'])
def route() -> str:
    return 'Hello, world!'


'''
Endpoints for LINE Bot
'''


@app.route('/callback', methods=['POST'])
def callback() -> str:
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


'''
handle event
'''


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: Event) -> None:
    handle_event(event, get_text_message_use_case(event))


@handler.add(FollowEvent)
def handle_follow(event: Event) -> None:
    handle_event(event, follow_use_case)


@handler.add(UnfollowEvent)
def handle_unfollow(event: Event) -> None:
    handle_event(event, unfollow_use_case)


@handler.add(JoinEvent)
def handle_join(event: Event) -> None:
    handle_event(event, join_use_case)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event: Event) -> None:
    handle_event(event, image_message_use_case)


@handler.add(PostbackEvent)
def handle_postback(event: Event) -> None:
    handle_event(event, postback_use_case)


def handle_event(event: Event, use_case: IUseCase):
    try:
        line_request_service.set_req_info(event)
        use_case.execute()
    except BaseException as err:
        print(traceback.format_exc())
        line_response_service.reset()
        line_response_service.add_message('サーバーエラーが発生しました。')
        line_response_service.add_message(str(err))
    line_response_service.reply(event)
    line_request_service.delete_req_info()


def get_text_message_use_case(event: Event):

    train_keywords: Dict[str, Callable] = {
        '遅延': reply_train_delay_use_case,
    }
    weather_keywords: Dict[str, Callable] = {
        '天気': reply_weather_use_case,
    }
    stock_keywords: Dict[str, Callable] = {
        '食材登録': register_stock_use_case,
        '食材一覧': reply_stock_use_case,
    }

    keyword = event.message.text.split()[0]
    # 電車情報
    if keyword in train_keywords:
        return train_keywords[keyword]
    # 天気情報
    elif keyword in weather_keywords:
        return weather_keywords[keyword]
    # 食材情報
    elif keyword in stock_keywords:
        return stock_keywords[keyword]
    else:
        return text_message_use_case
