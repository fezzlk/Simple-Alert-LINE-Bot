from abc import ABCMeta, abstractmethod
from typing import Dict, List
from src.Domains.Entities.WebUser import WebUser


class IWebUserRepository(metaclass=ABCMeta):

    @abstractmethod
    def create(
        self,
        new_web_user: WebUser,
    ) -> WebUser:
        pass

    @abstractmethod
    def update(
        self,
        query: Dict[str, any],
        new_web_user: WebUser,
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
    ) -> List[WebUser]:
        pass
