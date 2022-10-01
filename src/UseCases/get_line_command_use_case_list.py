from src.UseCases.Line.AddStockUseCase import AddStockUseCase
from src.UseCases.Line.ReplyStockUseCase import ReplyStockUseCase
from src.UseCases.Line.ReplyWebAppUrlUseCase import ReplyWebAppUrlUseCase

from src.UseCases.Line.RequestLinkLineWebUseCase import RequestLinkLineWebUseCase

from typing import Callable, Dict


def get_line_command_use_case_list() -> Dict[str, Dict[str, Callable]]:
    return {
        'stock_keywords': {
            '登録': AddStockUseCase(),
            '一覧': ReplyStockUseCase(),
        },
        'system_keywords': {
            'アカウント連携': RequestLinkLineWebUseCase(),
            'URL': ReplyWebAppUrlUseCase()
        }
    }
