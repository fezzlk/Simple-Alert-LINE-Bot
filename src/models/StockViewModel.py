from dataclasses import dataclass
from src.Domains.Entities.Stock import Stock

keys = [
    'item_name',
    'str_created_at',
    'str_expiry_date',
    'notify_status',
]
labels = ['名前', '登録日', '期限', '通知']


@dataclass()
class StockViewModel:
    _id: str
    item_name: str
    str_expiry_date: str
    str_created_at: str
    notify_status: str

    def __init__(
        self,
        _id: str = '',
        item_name: str = '',
        str_expiry_date: str = '',
        str_created_at: str = '',
        notify_status: str = '',
        stock: Stock = None
    ):
        if stock is not None:
            self._id = '' if stock._id is None else stock._id
            self.item_name = '' if stock.item_name is None else stock.item_name
            self.str_expiry_date = '' if stock.expiry_date is None else stock.expiry_date.date(
            ).strftime('%Y/%m/%d')
            self.str_created_at = '' if stock.created_at is None else stock.created_at.date(
            ).strftime('%Y/%m/%d')
            self.notify_status = 'ON' if stock.notify_enabled else 'OFF'
        else:
            self._id = _id
            self.item_name = item_name
            self.str_expiry_date = str_expiry_date
            self.str_created_at = str_created_at
            self.notify_status = notify_status
