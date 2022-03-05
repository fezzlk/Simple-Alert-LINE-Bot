from typing import Dict, List
from src.Domains.Entities.WebUser import WebUser
from src.mongo_client import mongo_client
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from datetime import datetime


class WebUserRepository(IWebUserRepository):

    def create(
        self,
        new_web_user: WebUser,
    ) -> WebUser:
        web_user_dict = new_web_user.__dict__.copy()
        if web_user_dict['_id'] is None:
            web_user_dict.pop('_id')
        result = mongo_client.db.web_users.insert_one(web_user_dict)
        new_web_user._id = result.inserted_id
        return new_web_user

    def update(
        self,
        query: Dict[str, any],
        new_values: Dict[str, any],
    ) -> int:
        new_values['updated_at'] = datetime.now()
        result = mongo_client.db.web_users.update_one(
            query, {'$set': new_values})
        return result.matched_count

    def find(
        self,
        query: Dict[str, any] = {},
    ) -> List[WebUser]:
        records = mongo_client.db.web_users.find(filter=query)
        web_users = []
        for record in records:
            record['_id'] = str(record['_id'])
            web_users.append(WebUser(**record))
        return web_users

    def delete(
        self,
        query: Dict[str, any] = {},
    ) -> int:
        result = mongo_client.db.web_users.delete_many(filter=query)
        return result.deleted_count

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> WebUser:
        domain = WebUser()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
