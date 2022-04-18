import traceback
from flask import Blueprint, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from src.Infrastructure.Repositories import line_user_repository
from src.services import line_request_service, line_response_service
from src.line_bot_api import handler

from src.UseCases.Line.FollowUseCase import FollowUseCase
from src.UseCases.Line.UnfollowUseCase import UnfollowUseCase
from src.UseCases.Line.JoinUseCase import JoinUseCase

from src.UseCases.Line.TextMessageUseCase import TextMessageUseCase
from src.UseCases.Line.ImageMessageUseCase import ImageMessageUseCase
from src.UseCases.Line.PostbackUseCase import PostbackUseCase

from src.UseCases.get_line_command_use_case_list import get_line_command_use_case_list
from src.UseCases.Line.ReplyHelpUseCase import ReplyHelpUseCase

from src import config
from linebot.models import (
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    MessageEvent,
    TextMessage,
    ImageMessage,
    PostbackEvent,
)

line_blueprint = Blueprint('line_blueprint', __name__, url_prefix='/')

'''
Endpoints for LINE Bot
'''


@line_blueprint.route('/callback', methods=['POST'])
def callback() -> str:
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print('Request body: ' + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


'''
handle event
'''

# 共通処理


def handle_event_decorater(function):
    def handle_event(*args, **kwargs):
        try:
            line_request_service.set_req_info(args[0])

            # LINE ユーザーの存在チェック
            line_users = line_user_repository.find({
                'line_user_id': line_request_service.req_line_user_id,
            })
            if len(line_users) == 0 and line_request_service.event_type != 'follow':
                line_response_service.add_message(
                    'まずは友達登録してください！')
            else:
                function(*args, **kwargs)

        except BaseException as err:
            traceback.print_exc()
            line_response_service.push_a_message(
                to=config.SERVER_ADMIN_LINE_USER_ID,
                message=str(err),
            )
            line_response_service.reset()
            line_response_service.add_message(text='システムエラーが発生しました。')

        line_response_service.reply(args[0])
        line_request_service.delete_req_info()

    return handle_event


@handler.add(MessageEvent, message=TextMessage)
@handle_event_decorater
def handle_message(event: Event, destination: str) -> None:
    get_use_case_text_message(event).execute()


@handler.add(FollowEvent)
@handle_event_decorater
def handle_follow(event: Event, destination: str) -> None:
    FollowUseCase().execute()


@handler.add(UnfollowEvent)
@handle_event_decorater
def handle_unfollow(event: Event, destination: str) -> None:
    UnfollowUseCase().execute()


@handler.add(JoinEvent)
@handle_event_decorater
def handle_join(event: Event, destination: str) -> None:
    JoinUseCase().execute()


@handler.add(MessageEvent, message=ImageMessage)
@handle_event_decorater
def handle_image_message(event: Event, destination: str) -> None:
    ImageMessageUseCase().execute()


@handler.add(PostbackEvent)
@handle_event_decorater
def handle_postback(event: Event, destination: str) -> None:
    PostbackUseCase().execute()


def get_use_case_text_message(event: Event):
    use_case_list = get_line_command_use_case_list()
    use_case_list['system_keywords']['ヘルプ'] = ReplyHelpUseCase()

    keyword = event.message.text.split()[0].upper()
    # 電車情報
    if keyword in use_case_list['train_keywords']:
        return use_case_list['train_keywords'][keyword]
    # 天気情報
    elif keyword in use_case_list['weather_keywords']:
        return use_case_list['weather_keywords'][keyword]
    # ストック情報
    elif keyword in use_case_list['stock_keywords']:
        return use_case_list['stock_keywords'][keyword]
    elif keyword in use_case_list['system_keywords']:
        return use_case_list['system_keywords'][keyword]
    else:
        return TextMessageUseCase()
