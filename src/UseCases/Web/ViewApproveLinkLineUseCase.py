from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.models.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.Infrastructure.Repositories import (
    line_user_repository,
)
from src.models.PageContents import PageContents


class ViewApproveLinkLineUseCase(IUseCase):
    def execute(self, page_contents: PageContents) -> Tuple[Dict, RegisterWebUserForm]:
        page_contents.page_title = 'LINEアカウント連携'

        web_user = page_contents.login_user
        line_users = line_user_repository.find(
            {'line_user_id': web_user.linked_line_user_id}
        )

        page_contents.line_user_name = line_users[0].line_user_name if len(
            line_users) != 0 else ''

        return page_contents
