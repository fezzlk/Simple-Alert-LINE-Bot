from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.Domains.Entities.User import User
from src.services import user_service


class FollowUseCase(IUseCase):
    def execute(self) -> None:
        name = line_request_service.req_line_user_name
        new_user = User(
            line_user_name=name,
            line_user_id=line_request_service.req_line_user_id,
        )
        user_service.find_or_create(new_user=new_user)
        line_response_service.add_message(f'{name}さん、友達登録ありがとうございます！')
