from flask import (
    request,
)
from werkzeug.exceptions import BadRequest

from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.services import web_user_service
from src.Infrastructure.Repositories import (
    web_user_repository,
)


class ApproveLinkLineUserUseCase(IUseCase):
    def execute(self, page_contents: dict) -> None:
        web_user_repository.update(
            {'web_user_email': page_contents['login_email']},
            {'is_linked_line_user': True},
        )
