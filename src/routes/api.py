from flask import Blueprint
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase
from src.UseCases.Line.CheckHabitTaskUseCase import CheckHabitTaskUseCase
from src.Infrastructure.Repositories import (
    habit_pending_confirmation_repository,
    habit_task_log_repository,
    habit_task_repository,
    line_user_repository,
    notification_schedule_repository,
    stock_repository,
    web_user_repository,
)
from src.services import line_response_service
api_blueprint = Blueprint('api_blueprint', __name__, url_prefix='/_api/v1')

'''
Endpoints for line push message
'''


@api_blueprint.route('/check_expire', methods=['post'])
def check_expire():
    CheckExpiredStockUseCase(
        notification_schedule_repository=notification_schedule_repository,
        web_user_repository=web_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    ).execute()
    return 'done'


@api_blueprint.route('/check_habit_tasks', methods=['post'])
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
