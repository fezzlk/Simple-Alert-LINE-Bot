from flask import request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from src import app
from src.line_bot_api import handler
from src.message import create_message
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
    handle_event(event)


@handler.add(FollowEvent)
def handle_follow(event):
    handle_event(event)


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    handle_event(event)


@handler.add(JoinEvent)
def handle_join(event):
    handle_event(event)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    handle_event(event)


@ handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    handle_event(event)


@ handler.add(PostbackEvent)
def handle_postback(event):
    handle_event(event)


def handle_event(event):
    try:
        line_request_service.set_req_info(event)
        create_message()
    except BaseException as err:
        print(err)
        line_response_service.add_message(str(err))
    line_response_service.reply(Event)
    line_request_service.delete_req_info()
