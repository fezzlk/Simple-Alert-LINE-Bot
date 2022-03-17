from flask import (
    request,
)
from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.models.PageContents import PageContents, RegisterFormData


class ViewRegisterUseCase(IUseCase):
    def execute(self, page_contents: PageContents[RegisterFormData]) -> Tuple[PageContents[RegisterFormData], RegisterWebUserForm]:
        page_contents.page_title = 'ユーザー登録'
        form = RegisterWebUserForm(request.form)

        form.web_user_name.data = page_contents.data.login_name
        form.web_user_email.data = page_contents.data.login_email

        return page_contents, form
