from flask import Blueprint
from src.UseCases.Stock.NotifyStockUseCase import NotifyStockUseCase
from src.UseCases.Stock.CheckExpiredStockUseCase import CheckExpiredStockUseCase
from src.services import line_response_service
api_blueprint = Blueprint('api_blueprint', __name__, url_prefix='/_api/v1')

'''
Endpoints for line push message
'''


@api_blueprint.route('/push_stock_info', methods=['post'])
def push_stock_info():
    NotifyStockUseCase().execute()
    return 'done'


@api_blueprint.route('/check_expire', methods=['post'])
def check_expire():
    CheckExpiredStockUseCase().execute()
    return 'done'
