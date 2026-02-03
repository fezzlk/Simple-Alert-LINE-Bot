from .LineRequestService import LineRequestService
from .LineResponseService import LineResponseService
from .LineUserService import LineUserService
from .WebUserService import WebUserService
from src.Infrastructure.Repositories import line_user_repository, web_user_repository

line_response_service = LineResponseService()
line_request_service = LineRequestService()
line_user_service = LineUserService(line_user_repository=line_user_repository)
web_user_service = WebUserService(web_user_repository=web_user_repository)
