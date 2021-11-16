from src.Domains.Entities.User import User
from src.pymongo import mongo_client


class UserRepository:

    def create(
        new_user: User,
    ) -> User:
        user_dict = new_user.__dict__.copy()
        if user_dict['_id'] is None:
            user_dict.pop('_id')
        result = mongo_client.db.users.insert_one(user_dict)
        new_user['_id'] = result.inserted_id
        return new_user
