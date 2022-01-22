from flask import (
    request,
    session,
)
from werkzeug.exceptions import BadRequest

from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.services import web_user_service


class RegisterWebUserUseCase(IUseCase):
    def execute(self) -> str:
        form = RegisterWebUserForm(request.form)
        form.web_user_email.data = None

        if not form.validate():
            raise BadRequest(
                ', '.join([f'{k}: {v}' for k, v in form.errors.items()]))

        new_web_user = WebUser(
            web_user_email=form.web_user_email.data,
            web_user_name=form.web_user_name.data,
        )
        web_user_service.find_or_create(new_web_user)
        return new_web_user.web_user_name
