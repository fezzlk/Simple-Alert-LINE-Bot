from src.Domains.Entities.Stock import Stock
from src.mongo_client import mongo_client
from src.Domains.IRepositories.IStockRepository import IStockRepository


class StockRepository(IStockRepository):

    def create(
        new_stock: Stock,
    ) -> Stock:
        stock_dict = new_stock.__dict__.copy()
        if stock_dict['_id'] is None:
            stock_dict.pop('_id')
        result = mongo_client.db.users.insert_one(stock_dict)
        new_stock['_id'] = result.inserted_id
        return new_stock
