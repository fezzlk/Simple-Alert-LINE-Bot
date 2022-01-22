from flask import (
    request,
    session,
)
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegistrationForm import RegistrationForm
from src.services import web_user_service


class RegisterWebUserUseCase(IUseCase):
    def execute(self) -> str:
        form = RegistrationForm(request.form)

        if not form.validate():
            return ''
        new_web_user = WebUser(
            web_user_email=form.web_user_email.data,
            web_user_name=form.web_user_name.data,
        )
        web_user_service.find_or_create(new_web_user)
        return new_web_user.web_user_name
