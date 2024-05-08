from abc import ABC, abstractmethod
import typing
from discordclient import BasicMessage


# This class exists solely to abstract away the implementation of a handler from discordclient.py
class Handler(ABC):

    @abstractmethod
    async def respond(self, message: BasicMessage) -> str | None:
        pass
