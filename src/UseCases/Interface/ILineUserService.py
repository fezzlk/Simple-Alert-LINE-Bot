from abc import ABCMeta, abstractmethod
from src.Domains.Entities.LineUser import LineUser


class ILineUserService(metaclass=ABCMeta):
    @abstractmethod
    def find_or_create(self, new_line_user: LineUser) -> LineUser:
        pass
