from src.Domains.Entities.User import User
from src.pymongo import mongo_client


class UserRepository:

    def create(
        new_user: User,
    ) -> User:
        # for i, v in new_user.__dict__.items():
        #     print(i)
        #     print(v)
        res = mongo_client.db.users.insert_one(new_user.__dict__)
        print("###")
        print(res)
        return new_user
