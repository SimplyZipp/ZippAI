import logging
import typing

from AbstractAPI import AbstractAPI
from memory.memory import Message
import asyncio


class TestAPI(AbstractAPI):

    def __init__(self):
        self.test_string = 'TestAPI'
        self.logger = logging.getLogger(__name__)
        self.sleep_time = 0.5

        # Mimic the generator returning empty strings
        # Makes the response echo the message, allowing for testing different strings
        self.blank = False

        # Mimic the API returning different errors
        self._val_err = False
        self._run_err = False

    @property
    def options(self) -> dict[str, typing.Any]:
        return {'test1': 'descript1', 'test2': 'descript2'}

    @property
    def presets(self) -> dict[str, dict[str, typing.Any]]:
        return {'Default': {'test1': 1, 'test2': 0.5}}

    async def get_response_structured(self, message: str, history: typing.List[Message] | None = None,
                                      indexes: typing.List[int] | None = None,
                                      options: dict[str, typing.Any] | None = None) -> str:
        if self._val_err:
            self._val_err = False
            raise ValueError('ValueError message')
        if self._run_err:
            self._run_err = False
            raise RuntimeError('RuntimeError message')
        for msg in history:
            if msg.tokens == 0:
                raise ValueError('Tokens not counted yet')
        if self.blank:
            return message
        return f'structured: {message}'

    async def count_tokens(self, text: Message) -> int:
        return await self.sleep(len(text.content))

    def get_response(self, s: str, stop: typing.List[str] | None = None, options: dict[str, typing.Any] | None = None) -> str:
        # Method not directly used by TextHandler
        if self.blank:
            return s
        return f'response: {s}'

    async def sleep(self, str_id: int) -> int:
        self.logger.info('Sleeping...')
        await asyncio.sleep(self.sleep_time)
        self.logger.info('Awake!')
        return str_id

    def set_sleep_time(self, time: float):
        self.sleep_time = time

    def trigger_value_error(self):
        self._val_err = True

    def trigger_runtime_error(self):
        self._run_err = True