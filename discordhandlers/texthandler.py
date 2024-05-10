import logging
import asyncio
import typing
import json
from configuration import Configuration
from jsoncustom.memoryjson import MemoryEncoder, MemoryDecoder
from AbstractAPI import AbstractAPI
from discordhandlers.abstracthandler import BasicMessage
from memory.memory import AbstractMemory, Message, Role
from memory.factories.memoryfactory import MemoryFactory
from memory.factories.factories import NoMemoryFactory  # To give a default factory if none specified
from discordhandlers.abstracthandler import Handler


class TextHandler(Handler):

    def __init__(self,
                 api: AbstractAPI,
                 memory_factory_lookup: dict[str, MemoryFactory],
                 *,
                 config: Configuration,
                 default_factory: MemoryFactory = NoMemoryFactory):
        self.api = api
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.memory_factory_lookup = memory_factory_lookup  # Used to change a memory type at runtime
        self.memories: dict[str, MemoryAndLock] = {}
        self.default_factory = default_factory

    async def respond(self, message: BasicMessage) -> str | None:

        # TODO: Sanitize
        # User messages need to be sanitized from harmful instructions or malicious requests
        # This is a difficult problem and very hard to solve.
        # Some ideas have been:
        #   1) Direct text search/manipulation using a filter
        #   2) Using an LLM to extract semantic meaning (also potentially vulnerable)
        #       -https://padolsey.medium.com/psa-always-sanitize-llm-user-inputs-cc0a38429e98
        #   3) Using LLM traps to see if user input triggers a warning
        #
        # For now, user messages are left completely un-sanitized. As for framework implementation,
        # the AbstractAPI should have a sanitize function of some sort.

        # TODO: Suppress warning/error messages
        # Make return type str | None
        # Return None if suppressed
        # Discord client needs to handle None

        async with self.lock(message.id):
            try:
                # Errors caught here and not inside the API because the messages shouldn't be saved
                msg = await self.api.get_response_structured(message.content,
                                                             history=self.memory(message.id).log,
                                                             indexes=self.memory(message.id).get_related_history(message.content),
                                                             options=self.config.get_active_options(message.guild_id, message.id))
            except ValueError as ex:
                self.logger.error(repr(ex))
                # Returned message doesn't use the error because this error shouldn't happen in the first place.
                # If it does, something in the code has gone wrong.
                return '[Internal error encountered during processing]'
            except RuntimeError as ex:
                # This error can happen, and is due to connection issues with the API
                self.logger.error(f'Encountered error while processing message {repr(message.content)}')
                return f'[{str(ex)}]'
        if len(msg.strip()) == 0:
            msg = '[No response]'

        # Save user message
        new_messages = [
            Message(role=Role.USER,
                    content=message.content,
                    tokens=0),
            Message(role=Role.ASSISTANT,
                    content=msg,
                    tokens=0)
        ]

        # Task is created and set to run, but never awaited because there is no return value
        task = asyncio.get_event_loop().create_task(self.message_work(new_messages, message.id))
        await asyncio.sleep(0)

        self.logger.info('Returning response')
        return msg

    async def message_work(self, msgs: typing.List[Message], memory_id: int) -> None:
        # An async lock is used to ensure this method finishes before another respond() can run
        async with self.lock(memory_id):
            self.logger.info('Getting token counts')
            task = asyncio.gather(self.api.count_tokens(msgs[0]),
                                  self.api.count_tokens(msgs[1]))
            for i in range(len(msgs)):
                self.memory(memory_id).add_log(msgs[i])
            tokens = await task
            for i in range(len(msgs)):
                msgs[i].tokens = tokens[i]
                self.logger.info(msgs[i])
            self.logger.info('Messages saved to memory')

    def _mem_and_lock(self, memory_id: int) -> 'MemoryAndLock':
        self.logger.debug(f'Accessing memory ID: {memory_id}')
        temp_id = str(memory_id)
        if temp_id not in self.memories:
            # Add a default memory
            self.logger.debug('Creating new memory')
            self.memories[temp_id] = MemoryAndLock(self.default_factory.make_memory())

        return self.memories[temp_id]

    def memory(self, memory_id: int) -> AbstractMemory:
        """
        Retrieve the memory associated with an ID
        :param memory_id: The ID to lookup
        :return: A subclass of AbstractMemory
        """
        meml = self._mem_and_lock(memory_id)
        return meml.memory

    def lock(self, memory_id: int) -> asyncio.Lock:
        """
        Retrieve the lock associated with a memory
        :param memory_id: The ID of the memory to lookup
        :return: An asyncio.Lock
        """
        meml = self._mem_and_lock(memory_id)
        return meml.lock

    async def get_options(self) -> typing.Iterable[str]:
        return self.api.options.keys()

    async def set_option(self, option: str, value: typing.Any, guild_id: int, channel_id: int) -> str | None:
        # TODO: Validation
        # Check for option validity and value validity depending on option
        # Probably best done using an object as described in a different to-do

        self.config.set_active_option(guild_id, channel_id, option, value)
        return None

    async def get_default_options(self) -> dict[str, typing.Any]:
        presets = self.api.presets
        return presets['Default'].copy()

    def save(self):
        self.logger.info('Saving memory')
        f = open('memory.txt', 'w')

        # Convert MemoryAndLock dict to AbstractMemory dict
        temp = {}
        for key, meml in self.memories.items():
            temp[key] = meml.memory

        f.write(json.dumps(temp, cls=MemoryEncoder, indent=2))
        f.close()

    def load(self) -> None:
        self.logger.info('Loading memory...')

        try:
            f = open('memory.txt', 'r')
            dump = f.read()
            temp: dict[str, AbstractMemory] = json.loads(dump, cls=MemoryDecoder)
            self.logger.debug(temp)

            # Convert AbstractMemory dict to MemoryAndLock dict
            for key, mem in temp.items():
                self.memories[key] = MemoryAndLock(mem)

        except Exception as ex:
            self.logger.error(repr(ex))
            self.logger.info('Using empty memory')
            # Currently just keeps an empty list which will overwrite unreadable json data
            # Might want to save old file under different name in case it's easily fixable


class MemoryAndLock:
    """
    A wrapper for TextHandler that includes a memory and its lock.
    The alternatives were a tuple or two dictionaries (with the same keys)
    """

    def __init__(self, memory: AbstractMemory):
        self.memory = memory
        self.lock = asyncio.Lock()
