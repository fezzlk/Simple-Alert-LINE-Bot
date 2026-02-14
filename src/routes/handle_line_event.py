import traceback
from flask import Blueprint, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from src.Infrastructure.Repositories import (
    habit_pending_confirmation_repository,
    habit_task_log_repository,
    habit_task_repository,
    line_user_repository,
    stock_repository,
    web_user_repository,
)
from src.services import (
    line_request_service,
    line_response_service,
    line_user_service,
    line_intent_parser_service,
    pending_line_operation_service,
)
from src.line_bot_api import handler

from src.UseCases.Line.FollowUseCase import FollowUseCase
from src.UseCases.Line.UnfollowUseCase import UnfollowUseCase
from src.UseCases.Line.JoinUseCase import JoinUseCase

from src.UseCases.Line.TextMessageUseCase import TextMessageUseCase
from src.UseCases.Line.ImageMessageUseCase import ImageMessageUseCase
from src.UseCases.Line.PostbackUseCase import PostbackUseCase

from src.UseCases.get_line_command_use_case_list import (
    get_line_command_use_case_list
)
from src.UseCases.Line.ReplyHelpUseCase import ReplyHelpUseCase
from src.UseCases.Line.HandleHabitTaskResponseUseCase import HandleHabitTaskResponseUseCase
from src.UseCases.Line.HandleIntentOperationUseCase import HandleIntentOperationUseCase
from src.services.LineIntentRulebook import (
    HELP_ALIASES,
    LIST_DISPLAY_ALIASES,
    LOGIN_ALIASES,
    WEB_LINK_ALIASES,
)

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

            # LINE アカウントの存在チェック
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
    FollowUseCase(
        line_request_service=line_request_service,
        line_response_service=line_response_service,
        line_user_service=line_user_service,
    ).execute()


@handler.add(UnfollowEvent)
@handle_event_decorater
def handle_unfollow(event: Event, destination: str) -> None:
    UnfollowUseCase(
        line_user_repository=line_user_repository,
        line_request_service=line_request_service,
    ).execute()


@handler.add(JoinEvent)
@handle_event_decorater
def handle_join(event: Event, destination: str) -> None:
    JoinUseCase(
        line_response_service=line_response_service,
    ).execute()


@handler.add(MessageEvent, message=ImageMessage)
@handle_event_decorater
def handle_image_message(event: Event, destination: str) -> None:
    ImageMessageUseCase(
        line_response_service=line_response_service,
    ).execute()


@handler.add(PostbackEvent)
@handle_event_decorater
def handle_postback(event: Event, destination: str) -> None:
    get_use_case_postback(event).execute()


def get_use_case_text_message(event: Event):
    use_case_list = get_line_command_use_case_list(
        stock_repository=stock_repository,
        web_user_repository=web_user_repository,
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )
    help_use_case = ReplyHelpUseCase(
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    message = event.message.text.strip()
    keyword = message.split()[0].upper() if message != '' else ''
    lower_message = message.lower()

    awaiting_other = habit_pending_confirmation_repository.find(
        {
            "line_user_id": line_request_service.req_line_user_id,
            "status": "awaiting_other_note",
        }
    )
    if event.source.type == 'user' and message != '' and len(awaiting_other) != 0:
        return HandleHabitTaskResponseUseCase(
            line_request_service=line_request_service,
            line_response_service=line_response_service,
            habit_task_repository=habit_task_repository,
            habit_task_log_repository=habit_task_log_repository,
            habit_pending_confirmation_repository=habit_pending_confirmation_repository,
        )

    if any(alias in message for alias in HELP_ALIASES):
        return help_use_case
    if any(alias in lower_message for alias in LOGIN_ALIASES):
        return use_case_list['system_keywords']['URL']
    # keep explicit commands direct
    if keyword in use_case_list['stock_keywords']:
        if event.source.type == 'user' and keyword == '登録':
            return HandleIntentOperationUseCase(
                stock_repository=stock_repository,
                line_request_service=line_request_service,
                line_response_service=line_response_service,
                intent_parser_service=line_intent_parser_service,
                pending_operation_service=pending_line_operation_service,
            )
        return use_case_list['stock_keywords'][keyword]
    elif keyword in use_case_list['system_keywords']:
        return use_case_list['system_keywords'][keyword]
    elif event.source.type == 'user' and message != '':
        parsed = line_intent_parser_service.parse(message)
        if parsed["intent"] == "help":
            return help_use_case
        if parsed["intent"] == "list":
            return use_case_list['stock_keywords']['一覧']
        if parsed["intent"] in ("web", "login"):
            return use_case_list['system_keywords']['URL']
        return HandleIntentOperationUseCase(
            stock_repository=stock_repository,
            line_request_service=line_request_service,
            line_response_service=line_response_service,
            intent_parser_service=line_intent_parser_service,
            pending_operation_service=pending_line_operation_service,
        )
    elif any(alias in message for alias in LIST_DISPLAY_ALIASES) or (
        '登録済み' in message and '一覧' in message
    ):
        return use_case_list['stock_keywords']['一覧']
    elif any(alias in lower_message for alias in WEB_LINK_ALIASES):
        return use_case_list['system_keywords']['URL']
    else:
        return TextMessageUseCase(
            line_response_service=line_response_service,
        )


def get_use_case_postback(event: Event):
    data = event.postback.data if hasattr(event, "postback") else ""
    if data.startswith("habit_confirm:"):
        return HandleHabitTaskResponseUseCase(
            line_request_service=line_request_service,
            line_response_service=line_response_service,
            habit_task_repository=habit_task_repository,
            habit_task_log_repository=habit_task_log_repository,
            habit_pending_confirmation_repository=habit_pending_confirmation_repository,
            postback_data=data,
        )
    if data == "intent_confirm:yes":
        line_request_service.message = "はい"
        return HandleIntentOperationUseCase(
            stock_repository=stock_repository,
            line_request_service=line_request_service,
            line_response_service=line_response_service,
            intent_parser_service=line_intent_parser_service,
            pending_operation_service=pending_line_operation_service,
        )
    if data == "intent_confirm:no":
        line_request_service.message = "いいえ"
        return HandleIntentOperationUseCase(
            stock_repository=stock_repository,
            line_request_service=line_request_service,
            line_response_service=line_response_service,
            intent_parser_service=line_intent_parser_service,
            pending_operation_service=pending_line_operation_service,
        )
    return PostbackUseCase(
        line_response_service=line_response_service,
    )
