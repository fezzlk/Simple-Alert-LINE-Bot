from src.UseCases.Web.ApproveLinkLineUserUseCase import ApproveLinkLineUserUseCase
from src.models.PageContents import PageContents
from src.Domains.Entities.WebUser import WebUser


class DummyWebUserRepository:
    def __init__(self):
        self.last_query = None
        self.last_values = None

    def update(self, query, new_values) -> int:
        self.last_query = query
        self.last_values = new_values
        return 1


def test_approve_line_user_use_case_updates_by_web_user_id(dummy_app):
    with dummy_app.test_request_context():
        repository = DummyWebUserRepository()
        use_case = ApproveLinkLineUserUseCase(web_user_repository=repository)
        page_contents = PageContents(
            session={
                "login_user": WebUser(
                    _id="W1",
                    web_user_name="dummy_web_user_1",
                    web_user_email="dummy1@example.com",
                    is_linked_line_user=False,
                )
            },
            request=dummy_app.test_request_context().request,
        )

        use_case.execute(page_contents=page_contents)

        assert repository.last_query == {"_id": "W1"}
        assert repository.last_values == {"is_linked_line_user": True}
