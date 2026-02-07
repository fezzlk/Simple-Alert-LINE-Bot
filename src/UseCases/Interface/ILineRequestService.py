from abc import ABCMeta, abstractmethod
from linebot.models.events import Event


class ILineRequestService(metaclass=ABCMeta):
    @property
    @abstractmethod
    def message(self) -> str:
        pass

    @property
    @abstractmethod
    def event_type(self) -> str:
        pass

    @property
    @abstractmethod
    def req_line_user_name(self) -> str:
        pass

    @property
    @abstractmethod
    def req_line_user_id(self) -> str:
        pass

    @property
    @abstractmethod
    def req_line_group_id(self) -> str:
        pass

    @abstractmethod
    def set_req_info(self, event: Event) -> None:
        pass

    @abstractmethod
    def delete_req_info(self) -> None:
        pass
