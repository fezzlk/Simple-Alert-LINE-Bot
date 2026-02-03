from flask import (
    request,
)
from werkzeug.exceptions import BadRequest

from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.models.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.UseCases.Interface.IWebUserService import IWebUserService
from src.models.PageContents import PageContents


class RegisterWebUserUseCase(IUseCase):
    def __init__(self, web_user_service: IWebUserService):
        self._web_user_service = web_user_service

    def execute(self, page_contents: PageContents) -> str:
        request = page_contents.request
        form = RegisterWebUserForm(request.form)

        if not form.validate():
            raise BadRequest(
                ', '.join([f'{k}: {v}' for k, v in form.errors.items()]))

        new_web_user = WebUser(
            web_user_email=form.web_user_email.data,
            web_user_name=form.web_user_name.data,
        )
        self._web_user_service.find_or_create(new_web_user)
        return new_web_user.web_user_name
