from src.Domains.Entities.LineUser import LineUser
from src.Infrastructure.Repositories import line_user_repository


class LineUserService:

    def find_or_create(self, new_line_user: LineUser) -> LineUser:
        """
            line user id で存在チェックし、同一アカウントが存在しなければ追加
        """

        record = line_user_repository.find(
            query={'line_user_id': new_line_user.line_user_id})

        if len(record) != 0:
            return new_line_user

        return line_user_repository.create(new_line_user=new_line_user)
