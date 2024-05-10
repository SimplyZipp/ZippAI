import logging
import typing
from AbstractAPI import AbstractAPI
import koboldai
from memory.memory import Message, Role
from httpx import HTTPStatusError


class KoboldAPI(AbstractAPI):

    # TODO: Create option details
    # Probably means creating an Option class with description and technical name
    # Subclasses can inherit and define more details like min/max, verify method
    # Should map user friendly name to Option
    OPTIONS = {
        'temperature': 'todo',
        'top_p': 'todo',
        'rep_pen': 'todo',
        'rep_pen_range': 'todo',
        'rep_pen_slope': 'todo',
        'top_k': 'todo',
        'top_a': 'todo',
        'typical': 'todo',
        'tfs': 'todo',
        'sampler_seed': 'todo',
        'sampler_order': 'The order by which all 7 samplers are applied. 0=top_k, 1=top_a, 2=top_p, 3=tfs, 4=typ, 5=temp, 6=rep_pen',
        'min_p': 'todo',
        'dynatemp_range': 'todo',
        'dynatemp_exponent': 'todo',
        'smoothing_factor': 'todo'
    }  # TODO: Mirostat

    # Default option presets
    PRESETS = {
        'Default':
            {
                'temperature': 0.7,
                'top_p': 0.92,
                'rep_pen': 1.1,
                'rep_pen_range': 320,
                'rep_pen_slope': 0.7,
                'top_k': 100,
                'top_a': 0,
                'typical': 1,
                'tfs': 1,
                'sampler_order': [6, 0, 1, 3, 4, 2, 5],
                'min_p': 0,
                'dynatemp_range': 0,
            }
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = koboldai.Client('http://localhost:5001')

        # Create blank lookup, then fill it in
        self.translate_role = ['' for _ in range(len(Role))]
        self.translate_role[Role.USER] = 'User'
        self.translate_role[Role.ASSISTANT] = 'ZippAI'

        # temp
        self.max_tokens = 2048
        self.max_length = 512

    @property
    def options(self) -> dict[str, typing.Any]:
        return self.OPTIONS

    @property
    def presets(self) -> dict[str, dict[str, typing.Any]]:
        return self.PRESETS

    async def get_response(self, s: str, stop: typing.List[str] | None = None, options: dict[str, typing.Any] | None = None) -> str:
        if stop is None:
            stop = []
        if options is None:
            options = self.PRESETS['Default']

        self.logger.info('Getting response using Kobold API')
        return await self.client.generate(s,
                                          max_length=200,
                                          **options,
                                          stop_sequence=stop)

    async def get_response_structured(self,
                                      message: str,
                                      history: typing.List[Message] | None = None,
                                      indexes: typing.List[int] | None = None,
                                      *,
                                      options: dict[str, typing.Any] | None = None) -> str:
        """
        Gets a response by structuring a response for the API, can also include a history

        :param message: The message to send to the AI
        :param history: The message log
        :param indexes: A list of indicies for the message log in order of importance. Messages are appended starting
        right above the new message. Ex: If the message history contains [past question, past response] and indexes is
        [1, 0], the order becomes [past question, past response, new message]
        :param options: Keyword options to give to the AI
        :return:
        """

        # I don't really like that the API needs to know about Message, but I don't know any other way to store
        # extra information like the role and token count such that:
        #   1) Memory stores the information outside the API
        #   2) The API can gain access to the information

        if history is None:
            history = []
            indexes = []

        initial_prompt = f'[The following is a chat message log between User and ZippAI. ZippAI follows instructions from User]\n\n' \
                         'User: Hi.\n' \
                         'ZippAI: Hello.'

        # Add user message and prompt the AI to respond
        message_log = [f'User: {message}\nZippAI: ']

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
                self.logger.debug(f'Max tokens reached. Current count: {tokens}')
                break
            message_log.append(f'{self.translate_role[msg.role]}: {msg.content}')

        message_log.append(initial_prompt)

        # Reverse the list because we need the most relevant things appended first and discard the rest
        prompt = '\n'.join(message_log[::-1])
        answer = await self.get_response(prompt, ['User:'], options)
        return answer.removesuffix('User:')

    async def count_tokens(self, text: Message) -> int:
        self.logger.debug(f'Counting tokens for "{text.content}"')
        return await self.client.tokencount(f'{self.translate_role[text.role]}: {text.content}')


if __name__ == '__main__':
    k = KoboldAPI()
    print(k.get_response_structured('Why is 42 the meaning of life? Where does it come from?'))
