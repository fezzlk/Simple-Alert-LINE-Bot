from flask import Blueprint
from src.UseCases.Line.CheckExpiredStockUseCase import CheckExpiredStockUseCase
api_blueprint = Blueprint('api_blueprint', __name__, url_prefix='/_api/v1')

'''
Endpoints for line push message
'''


@api_blueprint.route('/check_expire', methods=['post'])
def check_expire():
    CheckExpiredStockUseCase().execute()
    return 'done'
