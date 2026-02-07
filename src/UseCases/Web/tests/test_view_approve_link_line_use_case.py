from src.Domains.Entities.LineUser import LineUser
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.UseCases.Web.ViewApproveLinkLineUseCase import ViewApproveLinkLineUseCase
from src.models.PageContents import PageContents
from src.Domains.Entities.WebUser import WebUser


class DummyLineUserRepository(ILineUserRepository):
    def __init__(self, line_users: list[LineUser]):
        self._line_users = line_users

    def create(self, new_line_user: LineUser) -> LineUser:
        return new_line_user

    def update(self, query, new_line_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list[LineUser]:
        return self._line_users


def test_view_approve_link_line_user_sets_name(dummy_app):
    with dummy_app.test_request_context():
        web_user = WebUser(
            _id="W1",
            web_user_name="web",
            web_user_email="web@example.com",
            linked_line_user_id="U1",
            is_linked_line_user=True,
        )
        line_user = LineUser(
            line_user_name="line-name",
            line_user_id="U1",
        )
        page_contents = PageContents(
            session={"login_user": web_user},
            request=dummy_app.test_request_context().request,
        )
        use_case = ViewApproveLinkLineUseCase(
            line_user_repository=DummyLineUserRepository([line_user]),
        )

        result = use_case.execute(page_contents=page_contents)

        assert result.line_user_name == "line-name"
