from abc import ABC, abstractmethod
import typing
from memory.memory import Message


class AbstractAPI(ABC):

    @property
    @abstractmethod
    def options(self) -> dict[str, typing.Any]:
        pass

    @property
    @abstractmethod
    def presets(self) -> dict[str, dict[str, typing.Any]]:
        pass

    @abstractmethod
    async def get_response(self, s: str, stop: typing.List[str] | None = None, options: dict[str, typing.Any] | None = None) -> str:
        pass

    @abstractmethod
    async def get_response_structured(self,
                                      message: str,
                                      history: typing.List[Message] | None = None,
                                      indexes: typing.List[int] | None = None,
                                      *,
                                      options: dict[str, typing.Any] | None = None) -> str:
        pass

    @abstractmethod
    async def count_tokens(self, text: Message) -> int:
        """
        Returns the token count of a string using the chosen API's tokenizer.

        Implement this method if you want your API to access stored token counts in memory.
        Otherwise, ignore or just return 0.

        :param text: The text to count tokens
        :return:
        """
        return 0

    @staticmethod
    def estimate_tokens(text: str, method: typing.Literal['chars', 'words', 'avg'] = 'avg') -> int:
        # Might want to look into tiktoken to estimate tokens
        word_count = len(text.split(' '))
        char_count = len(text)
        tokens_word = word_count / 0.75
        tokens_char = char_count * 0.25

        if method == 'chars':
            return int(tokens_char)
        elif method == 'words':
            return int(tokens_word)
        elif method == 'avg':
            return int(tokens_char * 0.6 + tokens_word * 0.4)
