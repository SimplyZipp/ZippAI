import logging
import typing
from AbstractAPI import AbstractAPI
import koboldai
from memory.memory import Message, Role
from httpx import HTTPStatusError


class KoboldAPI(AbstractAPI):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = koboldai.Client('http://localhost:5001')
        self._options = {}

        # Create blank lookup, then fill it in
        self.translate_role = ['' for _ in range(len(Role))]
        self.translate_role[Role.USER] = 'User'
        self.translate_role[Role.ASSISTANT] = 'KoboldAI'

        # temp
        self.max_tokens = 2048
        self.max_length = 512

    @property
    def options(self) -> dict[str, typing.Any]:
        return self._options

    async def get_response(self, s: str, stop: typing.List[str] | None = None) -> str:
        if stop is None:
            stop = []

        self.logger.info('Getting response using Kobold API')
        return await self.client.generate(s,
                                          max_length=200,
                                          temperature=0.44,
                                          top_p=1,
                                          rep_pen=1.15,
                                          rep_pen_range=3,
                                          stop_sequence=stop)

    async def get_response_structured(self,
                                      message: str,
                                      history: typing.List[Message] | None = None,
                                      indexes: typing.List[int] | None = None) -> str:
        """
        Gets a response by structuring a response for the API, can also include a history

        :param message: The message to send to the AI
        :param history: The message log
        :param indexes: A list of indicies for the message log in order of importance. Messages are appended starting
        right above the new message. Ex: If the message history contains [past question, past response] and indexes is
        [1, 0], the order becomes [past question, past response, new message]
        :return:
        """

        # I don't really like that the API needs to know about Message, but I don't know any other way to store
        # extra information like the role and token count such that:
        #   1) Memory stores the information outside the API
        #   2) The API can gain access to the information

        if history is None:
            history = []
            indexes = []

        initial_prompt = f'[The following is a chat message log between User and KoboldAI. KoboldAI follows instructions from User]\n\n' \
                         'User: Hi.\n' \
                         'KoboldAI: Hello.'

        # Add user message and prompt the AI to respond
        message_log = [f'User: {message}\nKoboldAI: ']

        available_tokens = self.max_tokens - (self.max_length +
                                              self.estimate_tokens(initial_prompt) +
                                              self.estimate_tokens(message))

        tokens = 0
        for index in indexes:
            # Append history
            msg = history[index]
            if msg.tokens <= 0:
                raise ValueError('Message token count is 0')
            tokens += msg.tokens
            if tokens > available_tokens:
                break
            message_log.append(f'{self.translate_role[msg.role]}: {msg.content}')

        message_log.append(initial_prompt)

        # Reverse the list because we need the most relevant things appended first and discard the rest
        prompt = '\n'.join(message_log[::-1])
        answer = await self.get_response(prompt, ['User:'])
        return answer.removesuffix('User:')

    async def count_tokens(self, text: Message) -> int:
        self.logger.debug(f'Counting tokens for "{text.content}"')
        return await self.client.tokencount(f'{self.translate_role[text.role]}: {text.content}')


if __name__ == '__main__':
    k = KoboldAPI()
    print(k.get_response_structured('Why is 42 the meaning of life? Where does it come from?'))
