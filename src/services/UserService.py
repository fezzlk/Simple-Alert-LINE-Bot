from src.Domains.Entities.User import User
from src.Infrastructure.Repositories import user_repository


class UserService:

    def find_or_create(self, new_user: User) -> None:
        """
            line user id で存在チェックし、同一ユーザーが存在しなければ追加
        """

        record = user_repository.find(
            query={'line_user_id': new_user.line_user_id})

        if len(record) != 0:
            return new_user

        return user_repository.create(new_user=new_user)
