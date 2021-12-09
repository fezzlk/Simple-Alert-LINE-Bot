from .LineUserRepository import LineUserRepository
from .StockRepository import StockRepository
from .WebUserRepository import WebUserRepository

web_user_repository = WebUserRepository()
line_user_repository = LineUserRepository()
stock_repository = StockRepository()
