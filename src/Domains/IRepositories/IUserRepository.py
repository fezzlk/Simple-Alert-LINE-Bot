from abc import ABCMeta, abstractmethod
from typing import Dict, List
from src.Domains.Entities.User import User


class IUserRepository(metaclass=ABCMeta):

    @abstractmethod
    def create(
        self,
        new_user: User,
    ) -> User:
        pass

    # @abstractmethod
    # def update(
    #     self,
    #     user: User,
    # ) -> User:
    #     pass

    @abstractmethod
    def delete(
        self,
        query: Dict[str, any],
    ) -> bool:
        pass

    # @abstractmethod
    # def find_all(
    #     self,
    # ) -> List[User]:
    #     pass

    @abstractmethod
    def find(
        self,
        query: Dict[str, any],
    ) -> List[User]:
        pass
