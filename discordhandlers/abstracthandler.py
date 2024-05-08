from abc import ABC, abstractmethod
import typing


class BasicMessage:

    def __init__(self, message: str, *, user: str, unique_id: int):
        self.content = message
        self.user = user
        self.id = unique_id


# This class exists solely to abstract away the implementation of a handler from discordclient.py
class Handler(ABC):

    @abstractmethod
    async def respond(self, message: BasicMessage) -> str | None:
        pass
