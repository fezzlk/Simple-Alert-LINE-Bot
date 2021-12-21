from typing import Dict, List
from src.Domains.Entities.LineUser import LineUser
from src.mongo_client import mongo_client
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository


class LineUserRepository(ILineUserRepository):

    def create(
        self,
        new_line_user: LineUser,
    ) -> LineUser:
        line_user_dict = new_line_user.__dict__.copy()
        if line_user_dict['_id'] is None:
            line_user_dict.pop('_id')
        result = mongo_client.db.line_users.insert_one(line_user_dict)
        new_line_user._id = result.inserted_id
        return new_line_user

    def update(
        self,
        query: Dict[str, any],
        new_values: Dict[str, any],
    ) -> int:
        result = mongo_client.db.line_users.update_one(
            query, {'$set': new_values})
        return result.matched_count

    def find(
        self,
        query: Dict[str, any] = {},
    ) -> List[LineUser]:
        records: dict = mongo_client.db.line_users.find(filter=query)
        line_users = []
        for record in records:
            record['_id'] = str(record['_id'])
            line_users.append(LineUser(**record))
        return line_users

    def delete(
        self,
        query: Dict[str, any] = {},
    ) -> int:
        result = mongo_client.db.line_users.delete_many(filter=query)
        return result.deleted_count

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> LineUser:
        domain = LineUser()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
