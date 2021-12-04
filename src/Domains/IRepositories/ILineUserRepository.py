from abc import ABCMeta, abstractmethod
from typing import Dict, List
from src.Domains.Entities.LineUser import LineUser


class ILineUserRepository(metaclass=ABCMeta):

    @abstractmethod
    def create(
        self,
        new_line_user: LineUser,
    ) -> LineUser:
        pass

    @abstractmethod
    def update(
        self,
        query: Dict[str, any],
        new_line_user: LineUser,
    ) -> int:
        pass

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
    ) -> List[LineUser]:
        pass
