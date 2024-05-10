from abc import ABC, abstractmethod
import typing


class BasicMessage:

    def __init__(self, message: str, *, user: str, guild_id: int, channel_id):
        self.content = message
        self.user = user
        self.id = channel_id
        self.guild_id = guild_id


# This class exists solely to abstract away the implementation of a handler from discordclient.py
class Handler(ABC):

    @abstractmethod
    async def respond(self, message: BasicMessage) -> str | None:
        pass

    @abstractmethod
    async def get_options(self) -> typing.List[str]:
        pass

    @abstractmethod
    async def set_option(self, option: str, value: typing.Any, guild_id: int, channel_id: int) -> str | None:
        pass

    @abstractmethod
    async def get_default_options(self) -> dict[str, typing.Any]:
        pass
