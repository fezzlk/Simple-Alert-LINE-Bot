from typing import Dict, List
from src.Domains.Entities.User import User
from src.mongo_client import mongo_client
from src.Domains.IRepositories.IUserRepository import IUserRepository


class UserRepository(IUserRepository):

    def create(
        self,
        new_user: User,
    ) -> User:
        user_dict = new_user.__dict__.copy()
        if user_dict['_id'] is None:
            user_dict.pop('_id')
        result = mongo_client.db.users.insert_one(user_dict)
        new_user._id = result.inserted_id
        return new_user

    def find(
        self,
        query: Dict[str, any] = {},
    ) -> List[User]:
        records = mongo_client.db.users.find(filter=query)
        users = []
        for record in records:
            users.append(User(**record))
        return users

    def delete(
        self,
        query: Dict[str, any],
    ) -> bool:
        print('delete')

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> User:
        domain = User()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
