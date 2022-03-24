from flask import session, request
from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.UseCases.Web.ApproveLinkLineUserUseCase import (
    ApproveLinkLineUserUseCase
)
from src.models.PageContents import PageContents
from src.Domains.Entities.WebUser import WebUser


dummy_web_user = WebUser(
    _id='U0123456789abcdefghijklmnopqrstu1',
    web_user_name='dummy_web_user_1',
    web_user_email='dummy1@example.com',
    is_linked_line_user=False,
)


def test_success(dummy_app):
    with dummy_app.test_request_context():
        # Arrange
        use_case = ApproveLinkLineUserUseCase()
        repository = WebUserRepository()
        repository.create(dummy_web_user)
        session['login_user'] = dummy_web_user

        page_contents = PageContents(session, request)

        # Act
        use_case.execute(page_contents=page_contents)

        # Assert
        data = repository.find()
        assert data[0].is_linked_line_user
