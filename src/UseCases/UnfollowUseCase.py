from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
    line_request_service,
)
from src.Infrastructure.Repositories import user_repository


class UnfollowUseCase(IUseCase):
    def execute(self) -> None:
        user_repository.delete_by_line_user_id(
            line_request_service.req_line_user_id)
        line_response_service.isAbleToReply = False
