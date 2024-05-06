import logging
import typing
from typing import Any
from memory.memory import AbstractMemory, Message
import json


class BasicMemory(AbstractMemory):

    def __init__(self):
        # log order:
        #   0 - oldest log
        #   n - newest log
        self._log: typing.List[Message] = []
        self.logger = logging.getLogger(__name__)

    @property
    def log(self) -> typing.List[Message]:
        return self._log

    def add_log(self, message: Message) -> None:
        self._log.append(message)

    def get_related_history(self, message: str) -> typing.List[int]:
        # Return reverse chronological order (newest information first)
        return [i for i in range(len(self._log) - 1, -1, -1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            '__class__': 'BasicMemory',
            'log': [o.to_dict() for o in self._log]
        }

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> 'BasicMemory':
        mem = cls()
        for msg_dct in dictionary['log']:
            if msg_dct is None:
                continue
            mem.add_log(Message.from_dict(msg_dct))
        return mem
