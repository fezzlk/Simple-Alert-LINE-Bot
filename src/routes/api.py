from datetime import datetime

from flask import Blueprint, Response, abort

from src.Infrastructure.Repositories import (
    habit_pending_confirmation_repository,
    habit_task_log_repository,
    habit_task_repository,
    line_user_repository,
    notification_schedule_repository,
    stock_repository,
    web_user_repository,
)
from src.middlewares.api_auth import internal_api_auth_required
from src.services import line_response_service
from src.services.HabitCalendarImageService import build_week_dates, render_habit_calendar_image
from src.services.HabitCalendarTokenService import verify_token
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase
from src.UseCases.Line.CheckHabitTaskUseCase import CheckHabitTaskUseCase
from src.UseCases.Line.SendWeeklyHabitCalendarUseCase import SendWeeklyHabitCalendarUseCase

api_blueprint = Blueprint('api_blueprint', __name__, url_prefix='/_api/v1')

'''
Endpoints for line push message
'''


@api_blueprint.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200


@api_blueprint.route('/check_expire', methods=['post'])
@internal_api_auth_required
def check_expire():
    CheckExpiredStockUseCase(
        notification_schedule_repository=notification_schedule_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    ).execute()
    return 'done'


@api_blueprint.route('/check_habit_tasks', methods=['post'])
@internal_api_auth_required
def check_habit_tasks():
    CheckHabitTaskUseCase(
        line_user_repository=line_user_repository,
        web_user_repository=web_user_repository,
        habit_task_repository=habit_task_repository,
        habit_task_log_repository=habit_task_log_repository,
        habit_pending_confirmation_repository=habit_pending_confirmation_repository,
        line_response_service=line_response_service,
    ).execute()
    return 'done'


@api_blueprint.route('/send_weekly_habit_calendar', methods=['post'])
@internal_api_auth_required
def send_weekly_habit_calendar():
    # Cloud Scheduler 等から週次で叩かれる想定（トリガー自体は本リポジトリ外で設定する）。
    SendWeeklyHabitCalendarUseCase(
        line_user_repository=line_user_repository,
        web_user_repository=web_user_repository,
        habit_task_repository=habit_task_repository,
        line_response_service=line_response_service,
    ).execute()
    return 'done'


@api_blueprint.route('/habit_calendar/<token>.png', methods=['GET'])
def habit_calendar_image(token):
    '''
    LINE の ImageSendMessage は公開URLを要求するため、署名付きトークンで
    line_user_id・対象週・有効期限を検証したうえで画像をオンザフライ生成して返す。
    署名不一致・期限切れの場合は詳細を漏らさず 404 を返す。
    '''
    verified = verify_token(token)
    if verified is None:
        abort(404)
    line_user_id, week_start_date = verified

    try:
        week_start = datetime.strptime(week_start_date, '%Y-%m-%d').date()
    except ValueError:
        abort(404)

    web_users = web_user_repository.find(
        {
            'linked_line_user_id': line_user_id,
            'is_linked_line_user': True,
        }
    )
    linked_web_user_id = web_users[0]._id if len(web_users) != 0 else ''

    tasks = habit_task_repository.find(
        {
            'owner_id__in': [line_user_id, linked_web_user_id],
            'is_active': True,
        }
    )
    if len(tasks) == 0:
        abort(404)

    week_dates = build_week_dates(week_start)
    task_rows = []
    for task in tasks:
        results = {}
        for day in week_dates:
            scheduled_date = day.strftime('%Y-%m-%d')
            logs = habit_task_log_repository.find(
                {'habit_task_id': task._id, 'scheduled_date': scheduled_date}
            )
            results[scheduled_date] = logs[0].result if len(logs) != 0 else None
        task_rows.append({'task_name': task.task_name, 'results': results})

    png_bytes = render_habit_calendar_image(task_rows, week_dates)
    return Response(png_bytes, mimetype='image/png')
