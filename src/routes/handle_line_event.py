import traceback
from typing import Callable, Dict
from flask import Blueprint, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from src.Infrastructure.Repositories import line_user_repository
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import line_request_service, line_response_service
from src.line_bot_api import handler

from src.UseCases.Line.FollowUseCase import FollowUseCase
from src.UseCases.Line.UnfollowUseCase import UnfollowUseCase
from src.UseCases.Line.JoinUseCase import JoinUseCase

from src.UseCases.Line.TextMessageUseCase import TextMessageUseCase
from src.UseCases.Line.ImageMessageUseCase import ImageMessageUseCase
from src.UseCases.Line.PostbackUseCase import PostbackUseCase

from src.UseCases.Line.ReplyTrainDelayUseCase import ReplyTrainDelayUseCase

from src.UseCases.Line.ReplyWeatherUseCase import ReplyWeatherUseCase

from src.UseCases.Line.RegisterStockUseCase import RegisterStockUseCase
from src.UseCases.Line.ReplyStockUseCase import ReplyStockUseCase

from src.UseCases.Line.RequestLinkLineWebUseCase import RequestLinkLineWebUseCase

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
            print(traceback.format_exc())
            line_response_service.reset()
            line_response_service.add_message(
                'エラーが発生しました。もしよければ Bug として起票してください。')
            line_response_service.add_message(
                'https://github.com/fezzlk/Simple-Alert-LINE-Bot/issues/new')

        line_response_service.reply(args[0])
        line_request_service.delete_req_info()

    return handle_event


@handler.add(MessageEvent, message=TextMessage)
@handle_event_decorater
def handle_message(event: Event, destination: str) -> None:
    get_text_message_use_case(event).execute()


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


def get_text_message_use_case(event: Event):

    train_keywords: Dict[str, Callable] = {
        '遅延': ReplyTrainDelayUseCase(),
    }
    weather_keywords: Dict[str, Callable] = {
        '天気': ReplyWeatherUseCase(),
    }
    stock_keywords: Dict[str, Callable] = {
        'ストック登録': RegisterStockUseCase(),
        'ストック一覧': ReplyStockUseCase(),
    }
    system_keywords: Dict[str, Callable] = {
        'ユーザー連携': RequestLinkLineWebUseCase(),
    }

    keyword = event.message.text.split()[0]
    # 電車情報
    if keyword in train_keywords:
        return train_keywords[keyword]
    # 天気情報
    elif keyword in weather_keywords:
        return weather_keywords[keyword]
    # ストック情報
    elif keyword in stock_keywords:
        return stock_keywords[keyword]
    elif keyword in system_keywords:
        return system_keywords[keyword]
    else:
        return TextMessageUseCase
