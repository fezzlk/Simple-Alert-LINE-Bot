from typing import Dict, List, Tuple
from src.Domains.Entities.Stock import Stock
from src.mongo_client import mongo_client
from src.Domains.IRepositories.IStockRepository import IStockRepository
from pymongo import ASCENDING, DESCENDING
from datetime import datetime


class StockRepository(IStockRepository):

    def create(
        self,
        new_stock: Stock,
    ) -> Stock:
        stock_dict = new_stock.__dict__.copy()
        if stock_dict['_id'] is None:
            stock_dict.pop('_id')
        result = mongo_client.db.stocks.insert_one(stock_dict)
        new_stock._id = result.inserted_id
        return new_stock

    def update(
        self,
        query: Dict[str, any],
        new_values: Dict[str, any],
    ) -> int:
        new_values['updated_at'] = datetime.now()
        result = mongo_client.db.stocks.update_one(query, {'$set': new_values})
        return result.matched_count

    def find(
        self,
        query: Dict[str, any] = {},
        sort: List[Tuple[str, any]] = [('id', ASCENDING)],
    ) -> List[Stock]:
        records = mongo_client.db.stocks\
            .find(filter=query)\
            .sort(sort)
        stocks = []
        for record in records:
            record['_id'] = str(record['_id'])
            stocks.append(Stock(**record))
        return stocks

    def delete(
        self,
        query: Dict[str, any] = {},
    ) -> int:
        result = mongo_client.db.stocks.delete_many(filter=query)
        return result.deleted_count

    def _mapping_record_to_domain(self, record: Dict[str, any]) -> Stock:
        domain = Stock()
        for attr, value in record.items():
            domain.__setitem__(attr, value)
        return domain
