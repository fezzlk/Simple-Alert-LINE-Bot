from abc import ABCMeta, abstractmethod
from typing import Dict, List
from src.Domains.Entities.Stock import Stock


class IStockRepository(metaclass=ABCMeta):

    @abstractmethod
    def create(
        self,
        new_stock: Stock,
    ) -> Stock:
        pass

    # @abstractmethod
    # def update(
    #     self,
    #     stock: Stock,
    # ) -> Stock:
    #     pass

    @abstractmethod
    def delete(
        self,
        query: Dict[str, any],
    ) -> int:
        pass

    @abstractmethod
    def find(
        self,
        query: Dict[str, any],
    ) -> List[Stock]:
        pass
