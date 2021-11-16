from abc import ABCMeta, abstractmethod
from Domains.Entities.Stock import Stock


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

    # @abstractmethod
    # def delete(
    #     self,
    #     stock_id: str,
    # ) -> bool:
    #     pass

    # @abstractmethod
    # def find_all(
    #     self,
    # ) -> List[Stock]:
    #     pass

    # @abstractmethod
    # def find(
    #     self,
    #     query: Dict[str, any],
    # ) -> List[Stock]:
    #     pass
