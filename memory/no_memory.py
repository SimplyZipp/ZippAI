import logging
import typing
from typing import Any

from memory.memory import AbstractMemory, Message


class NoMemory(AbstractMemory):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @property
    def log(self) -> typing.List[Message]:
        return []

    def add_log(self, message: Message) -> None:
        pass

    def get_related_history(self, message: str) -> typing.List[int]:
        return []

    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> 'NoMemory':
        pass
