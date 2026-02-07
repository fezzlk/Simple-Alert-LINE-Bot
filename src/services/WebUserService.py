from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IWebUserService import IWebUserService
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository


class WebUserService(IWebUserService):
    def __init__(self, web_user_repository: IWebUserRepository):
        self._web_user_repository = web_user_repository

    def find_or_create(self, new_web_user: WebUser) -> WebUser:
        """
            email で存在チェックし、同一アカウントが存在しなければ追加
        """

        record = self._web_user_repository.find(
            query={'web_user_email': new_web_user.web_user_email})

        if len(record) != 0:
            return new_web_user

        return self._web_user_repository.create(new_web_user=new_web_user)
