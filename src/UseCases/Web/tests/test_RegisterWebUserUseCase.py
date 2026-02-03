import werkzeug
from typing import List
from flask import session, request
from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.UseCases.Web.RegisterWebUserUseCase import RegisterWebUserUseCase
from src.services.WebUserService import WebUserService
from src.models.PageContents import PageContents
from src.Domains.Entities.WebUser import WebUser

def generate_dummy_web_user_list() -> List[WebUser]:
    return [
        WebUser(
            _id='U0123456789abcdefghijklmnopqrstu1',
            web_user_name='dummy_web_user_1',
            web_user_email='dummy1@example.com',
        ),
    ]

def test_success(dummy_app):
    with dummy_app.test_request_context():
        # Arrange
        web_user_service = WebUserService(
            web_user_repository=WebUserRepository(),
        )
        use_case = RegisterWebUserUseCase(web_user_service=web_user_service)
        dummy_user = generate_dummy_web_user_list()[0]
        request.form = werkzeug.datastructures.ImmutableMultiDict({
            'web_user_name': dummy_user.web_user_name,
            'web_user_email': dummy_user.web_user_email,
        })
        page_contents = PageContents(session, request)

        # Act
        result = use_case.execute(page_contents=page_contents)

        # Assert
        assert result == dummy_user.web_user_name
        users_in_db = WebUserRepository().find()
        for user in users_in_db:
            assert user.web_user_name == dummy_user.web_user_name
            assert user.web_user_email == dummy_user.web_user_email
