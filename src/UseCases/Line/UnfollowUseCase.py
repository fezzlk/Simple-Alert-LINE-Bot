from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
)
from src.Infrastructure.Repositories import line_user_repository


class UnfollowUseCase(IUseCase):
    def execute(self) -> None:
        query = {'line_user_id': line_request_service.req_line_user_id}
        line_user_repository.delete(
            query=query,
        )
