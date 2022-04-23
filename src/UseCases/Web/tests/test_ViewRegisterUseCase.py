from typing import List
from flask import session, request
from src.UseCases.Web.ViewRegisterUseCase import ViewRegisterUseCase
from src.models.PageContents import PageContents, RegisterFormData
from src.Domains.Entities.WebUser import WebUser

from src.models.Forms.RegisterWebUserForm import RegisterWebUserForm


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
        use_case = ViewRegisterUseCase()
        dummy_user = generate_dummy_web_user_list()[0]
        session['login_name'] = dummy_user.web_user_name
        session['login_email'] = dummy_user.web_user_email
        page_contents = PageContents[RegisterFormData](
            session, request, RegisterFormData)

        # Act
        page_contents, form = use_case.execute(page_contents=page_contents)

        # Assert
        assert isinstance(page_contents, PageContents)
        assert page_contents.page_title == 'ユーザー登録'
        assert isinstance(form, RegisterWebUserForm)
        assert form.web_user_name.data == dummy_user.web_user_name
        assert form.web_user_email.data == dummy_user.web_user_email
