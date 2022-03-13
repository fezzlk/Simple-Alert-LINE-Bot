from flask import (
    request,
)
from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm


class ViewRegisterUseCase(IUseCase):
    def execute(self, page_contents: dict) -> Tuple[Dict, RegisterWebUserForm]:
        page_contents['title'] = 'ユーザー登録'

        form = RegisterWebUserForm(request.form)
        form.web_user_name.data = page_contents.get('login_name', '')
        form.web_user_email.data = page_contents.get('login_email', '')
        return page_contents, form
