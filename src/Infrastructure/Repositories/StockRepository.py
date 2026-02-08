from typing import Any, Dict, List, Tuple
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldPath
from src.Domains.Entities.Stock import Stock
from src.firestore_client import firestore_client
from src.firestore_query import build_filters
from src.Domains.IRepositories.IStockRepository import IStockRepository


class StockRepository(IStockRepository):
    _collection_name = 'stocks'

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

    def _apply_sort(self, query_ref, sort: List[Tuple[str, Any]]):
        for field, direction in sort:
            if field in ('_id', 'id'):
                field_ref = FieldPath.document_id()
            else:
                field_ref = field
            if direction in ('desc', 'descending', firestore.Query.DESCENDING):
                query_ref = query_ref.order_by(field_ref, direction=firestore.Query.DESCENDING)
            else:
                query_ref = query_ref.order_by(field_ref, direction=firestore.Query.ASCENDING)
        return query_ref

    def create(
        self,
        new_stock: Stock,
    ) -> Stock:
        stock_dict = new_stock.__dict__.copy()
        if stock_dict['_id'] is None:
            stock_dict.pop('_id')
            doc_ref = self._collection().document()
        else:
            doc_ref = self._collection().document(str(stock_dict['_id']))
        doc_ref.set(stock_dict)
        new_stock._id = doc_ref.id
        return new_stock

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
        sort: List[Tuple[str, any]] = [('id', 'asc')],
    ) -> List[Stock]:
        query_ref = self._apply_filters(self._collection(), query)
        query_ref = self._apply_sort(query_ref, sort)
        records = query_ref.stream()
        stocks = []
        for record in records:
            data = record.to_dict() or {}
            data['_id'] = record.id
            stocks.append(Stock(**data))
        return stocks

    def delete(
        self,
        query: Dict[str, any] = {},
    ) -> int:
        query_ref = self._apply_filters(self._collection(), query)
        docs = list(query_ref.stream())
        for doc in docs:
            doc.reference.delete()
        return len(docs)

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> Stock:
        domain = Stock()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
