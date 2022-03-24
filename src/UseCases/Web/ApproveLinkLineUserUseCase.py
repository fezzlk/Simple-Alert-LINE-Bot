from src.UseCases.Interface.IUseCase import IUseCase
from src.models.PageContents import PageContents
from src.Infrastructure.Repositories import (
    web_user_repository,
)


class ApproveLinkLineUserUseCase(IUseCase):
    def execute(self, page_contents: PageContents) -> None:
        web_user_repository.update(
            {'web_user_email': page_contents.login_user.web_user_email},
            {'is_linked_line_user': True},
        )
