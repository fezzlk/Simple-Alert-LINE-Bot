from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService


class UnfollowUseCase(IUseCase):
    def __init__(
        self,
        line_user_repository: ILineUserRepository,
        line_request_service: ILineRequestService,
    ):
        self._line_user_repository = line_user_repository
        self._line_request_service = line_request_service

    def execute(self) -> None:
        query = {'line_user_id': self._line_request_service.req_line_user_id}
        self._line_user_repository.delete(
            query=query,
        )
