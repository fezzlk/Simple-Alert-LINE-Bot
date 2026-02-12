from typing import Any, Dict, List
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.field_path import FieldPath
from src.Domains.Entities.LineUser import LineUser
from src.firestore_client import firestore_client
from src.firestore_query import build_filters
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository


class LineUserRepository(ILineUserRepository):
    _collection_name = 'line_users'

    def _collection(self):
        return firestore_client.collection(self._collection_name)

    def _apply_filters(self, query_ref, query: Dict[str, Any]):
        filters = build_filters(query)
        for field, op, value in filters:
            if field in ('_id', 'id'):
                field_ref = FieldPath.document_id()
            else:
                field_ref = field
            if op == 'in' and value == []:
                return query_ref.where(field_ref, '==', '__no_results__')
            query_ref = query_ref.where(field_ref, op, value)
        return query_ref

    def create(
        self,
        new_line_user: LineUser,
    ) -> LineUser:
        line_user_dict = new_line_user.__dict__.copy()
        if line_user_dict['_id'] is None:
            line_user_dict.pop('_id')
            doc_ref = self._collection().document()
        else:
            doc_ref = self._collection().document(str(line_user_dict['_id']))
        doc_ref.set(line_user_dict)
        new_line_user._id = doc_ref.id
        return new_line_user

    def update(
        self,
        query: Dict[str, any],
        new_values: Dict[str, any],
    ) -> int:
        new_values['updated_at'] = datetime.now()
        query_ref = self._apply_filters(self._collection(), query)
        docs = list(query_ref.stream())
        for doc in docs:
            doc.reference.update(new_values)
        return len(docs)

    def find(
        self,
        query: Dict[str, any] = {},
    ) -> List[LineUser]:
        query_ref = self._apply_filters(self._collection(), query)
        query_ref = query_ref.order_by('line_user_id', direction=firestore.Query.ASCENDING)
        records = query_ref.stream()
        line_users = []
        for record in records:
            data = record.to_dict() or {}
            data['_id'] = record.id
            line_users.append(LineUser(**data))
        return line_users

    def delete(
        self,
        query: Dict[str, any] = {},
    ) -> int:
        query_ref = self._apply_filters(self._collection(), query)
        docs = list(query_ref.stream())
        for doc in docs:
            doc.reference.delete()
        return len(docs)

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> LineUser:
        domain = LineUser()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
