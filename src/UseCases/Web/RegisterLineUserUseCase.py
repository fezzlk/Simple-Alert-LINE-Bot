from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository


class RegisterLineUserUseCase(IUseCase):
    def __init__(self, web_user_repository: IWebUserRepository):
        self._web_user_repository = web_user_repository

    def execute(self, line_user_id: str, web_user_name: str) -> WebUser:
        existing = self._web_user_repository.find(
            {'linked_line_user_id': line_user_id}
        )
        if len(existing) > 0:
            return existing[0]

        new_web_user = WebUser(
            web_user_name=web_user_name,
            web_user_email=None,
            linked_line_user_id=line_user_id,
            is_linked_line_user=True,
        )
        return self._web_user_repository.create(new_web_user=new_web_user)
