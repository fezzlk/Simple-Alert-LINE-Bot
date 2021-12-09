from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.oauth_client import oauth
from flask import session
from src.Infrastructure.Repositories import web_user_repository


class AfterLoginUseCase(IUseCase):
    def execute(self) -> None:
        google = oauth.create_client('google')
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        # do something with the token and profile
        email = user_info['email']
        user_name = user_info['name']
        session['login_email'] = email
        session['login_name'] = user_name
        session['login_picture'] = user_info['picture']
        session['access_token'] = token['access_token']
        session['id_token'] = token['id_token']

        # find_query クラス作る？
        users = web_user_repository.find({'web_user_email': email})
        if len(users) == 0:
            new_web_user = WebUser(
                web_user_name=user_name,
                web_user_email=email,
            )
            web_user_repository.create(new_web_user)
