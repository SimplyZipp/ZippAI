from abc import ABC, abstractmethod
import typing
from typing import Any
from enum import IntEnum


class Role(IntEnum):
    USER = 0
    ASSISTANT = 1


class Message:

    def __init__(self, *, role: Role, content: str, tokens: int = 0):
        self.role = role
        self.content = content
        self.tokens = tokens

    def __str__(self):
        return str(self.__dict__())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Message':
        return cls(role=data['role'],
                   content=data['content'],
                   tokens=data['tokens'])

    def to_dict(self) -> dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'tokens': self.tokens
        }

    def __dict__(self):
        return self.to_dict()


class AbstractMemory(ABC):

    @property
    @abstractmethod
    def log(self) -> typing.List[Message]:
        """
        Do not directly modify.

        :return:
        """
        pass

    @abstractmethod
    def add_log(self, message: Message) -> None:
        pass

    @abstractmethod
    def get_related_history(self, message: str) -> typing.List[int]:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> 'AbstractMemory':
        pass

    def __dict__(self):
        return self.to_dict()

