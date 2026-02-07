from src.UseCases.Line.AddStockUseCase import AddStockUseCase
from src.UseCases.Line.ReplyStockUseCase import ReplyStockUseCase
from src.UseCases.Line.ReplyWebAppUrlUseCase import ReplyWebAppUrlUseCase

from src.UseCases.Line.RequestLinkLineWebUseCase import RequestLinkLineWebUseCase

from typing import Callable, Dict
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


def get_line_command_use_case_list(
    stock_repository: IStockRepository,
    web_user_repository: IWebUserRepository,
    line_request_service: ILineRequestService,
    line_response_service: ILineResponseService,
) -> Dict[str, Dict[str, Callable]]:
    return {
        'stock_keywords': {
            '登録': AddStockUseCase(
                stock_repository=stock_repository,
                line_request_service=line_request_service,
                line_response_service=line_response_service,
            ),
            '一覧': ReplyStockUseCase(
                stock_repository=stock_repository,
                web_user_repository=web_user_repository,
                line_request_service=line_request_service,
                line_response_service=line_response_service,
            ),
        },
        'system_keywords': {
            'アカウント連携': RequestLinkLineWebUseCase(
                web_user_repository=web_user_repository,
                line_request_service=line_request_service,
                line_response_service=line_response_service,
            ),
            'URL': ReplyWebAppUrlUseCase(
                line_response_service=line_response_service,
            )
        }
    }
