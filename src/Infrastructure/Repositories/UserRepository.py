from src.Domains.Entities.User import User
from src.PyMongo import mongo_client
from src.Domains.IRepositories.IUserRepository import IUserRepository


class UserRepository(IUserRepository):

    def create(
        new_user: User,
    ) -> User:
        user_dict = new_user.__dict__.copy()
        if user_dict['_id'] is None:
            user_dict.pop('_id')
        result = mongo_client.db.users.insert_one(user_dict)
        new_user['_id'] = result.inserted_id
        return new_user
