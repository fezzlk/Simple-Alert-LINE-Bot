from src.UseCases.Interface.IUseCase import IUseCase
from src.models.PageContents import PageContents
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository


class ApproveLinkLineUserUseCase(IUseCase):
    def __init__(self, web_user_repository: IWebUserRepository):
        self._web_user_repository = web_user_repository

    def execute(self, page_contents: PageContents) -> None:
        self._web_user_repository.update(
            {'web_user_email': page_contents.login_user.web_user_email},
            {'is_linked_line_user': True},
        )
