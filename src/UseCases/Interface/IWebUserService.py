from abc import ABCMeta, abstractmethod
from src.Domains.Entities.WebUser import WebUser


class IWebUserService(metaclass=ABCMeta):
    @abstractmethod
    def find_or_create(self, new_web_user: WebUser) -> WebUser:
        pass
