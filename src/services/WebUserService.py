from src.Domains.Entities.WebUser import WebUser
from src.Infrastructure.Repositories import web_user_repository


class WebUserService:

    def find_or_create(self, new_web_user: WebUser) -> WebUser:
        """
            email で存在チェックし、同一ユーザーが存在しなければ追加
        """

        record = web_user_repository.find(
            query={'web_user_email': new_web_user.web_user_id})

        if len(record) != 0:
            return new_web_user

        return web_user_repository.create(new_web_user=new_web_user)
