from abc import ABCMeta, abstractmethod
from linebot.models.events import Event


class ILineResponseService(metaclass=ABCMeta):
    @abstractmethod
    def add_message(self, text: str) -> None:
        pass

    @abstractmethod
    def add_image(self, image_url: str) -> None:
        pass

    @abstractmethod
    def reply(self, event: Event) -> None:
        pass

    @abstractmethod
    def push(self, to: str) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def push_a_message(self, to: str, message: str) -> None:
        pass
