from flask import Blueprint
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase
from src.Infrastructure.Repositories import line_user_repository, stock_repository
from src.services import line_response_service
api_blueprint = Blueprint('api_blueprint', __name__, url_prefix='/_api/v1')

'''
Endpoints for line push message
'''


@api_blueprint.route('/check_expire', methods=['post'])
def check_expire():
    CheckExpiredStockUseCase(
        line_user_repository=line_user_repository,
        stock_repository=stock_repository,
        line_response_service=line_response_service,
    ).execute()
    return 'done'
