from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.Entities.WebUser import WebUser
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.Infrastructure.Repositories import (
    line_user_repository,
)


class ViewApproveLinkLineUseCase(IUseCase):
    def execute(self, page_contents: dict) -> Tuple[Dict, RegisterWebUserForm]:
        page_contents['title'] = 'LINEユーザー連携'

        web_user: WebUser = page_contents['login_user']
        line_users = line_user_repository.find(
            {'line_user_id': web_user.linked_line_user_id}
        )

        page_contents['line_user_name'] = line_users[0].line_user_name if len(
            line_users) != 0 else ''

        return page_contents
