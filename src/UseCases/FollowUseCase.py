from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.Domains.Entities.LineUser import LineUser
from src.services import line_user_service


class FollowUseCase(IUseCase):
    def execute(self) -> None:
        name = line_request_service.req_line_user_name
        new_line_user = LineUser(
            line_user_name=name,
            line_user_id=line_request_service.req_line_user_id,
        )
        line_user_service.find_or_create(new_line_user=new_line_user)
        line_response_service.add_message(f'{name}さん、友達登録ありがとうございます！')
