from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.models.PageContents import PageContents


class ViewApproveLinkLineUseCase(IUseCase):
    def __init__(self, line_user_repository: ILineUserRepository):
        self._line_user_repository = line_user_repository

    def execute(self, page_contents: PageContents) -> PageContents:
        page_contents.page_title = "LINEアカウント連携"
        page_contents.line_user_name = ""
        page_contents.line_link_status = "none"

        web_user = page_contents.login_user
        if web_user is None:
            return page_contents
        if web_user.is_linked_line_user:
            page_contents.line_link_status = "linked"
        if not web_user.linked_line_user_id:
            return page_contents

        line_users = self._line_user_repository.find(
            {"line_user_id": web_user.linked_line_user_id}
        )
        if len(line_users) != 0:
            page_contents.line_user_name = line_users[0].line_user_name

        if not web_user.is_linked_line_user and page_contents.line_user_name:
            page_contents.line_link_status = "pending"
        return page_contents
