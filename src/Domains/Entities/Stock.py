from dataclasses import dataclass
from datetime import datetime

STOCK_STATUS = ['disabled', 'active', 'archived']


@dataclass()
class Stock:
    _id: str
    goods_name: str
    owner_id: str
    expiry_date: datetime
    status: int
    created_at: datetime
    updated_at: datetime


def __init__(
    self,
    _id: str = None,
    goods_name: str = 'unknown',
    owner_id: str = 'unknown',
    expiry_date: datetime = None,
    status: int = 0,
    created_at: datetime = datetime.now(),
    updated_at: datetime = datetime.now(),
):
    self._id = _id
    self.goods_name = goods_name
    self.owner_id = owner_id
    self.expiry_date = expiry_date
    self.status = status
    self.created_at = created_at
    self.updated_at = updated_at
