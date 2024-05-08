import logging
import asyncio
import typing
import json
from jsoncustom.memoryjson import MemoryEncoder, MemoryDecoder
from AbstractAPI import AbstractAPI
from discordclient import BasicMessage
from memory.memory import AbstractMemory, Message, Role
from memory.factories.memoryfactory import MemoryFactory
from discordhandlers.abstracthandler import Handler


class TextHandler(Handler):

    def __init__(self, api: AbstractAPI, memory_factory: MemoryFactory):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.memory_factory_lookup = None
        self.memory: AbstractMemory = memory_factory.make_memory()
        self.mem_lock = asyncio.Lock()

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

        async with self.mem_lock:
            try:
                # Errors caught here and not inside the API because the messages shouldn't be saved
                msg = await self.api.get_response_structured(message.content,
                                                             history=self.memory.log,
                                                             indexes=self.memory.get_related_history(message.content))
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
        task = asyncio.get_event_loop().create_task(self.message_work(new_messages))
        await asyncio.sleep(0)

        self.logger.info('Returning response')
        return msg

    async def message_work(self, msgs: typing.List[Message]) -> None:
        # An async lock is used to ensure this method finishes before another respond() can run
        async with self.mem_lock:
            self.logger.info('Getting token counts')
            task = asyncio.gather(self.api.count_tokens(msgs[0]),
                                  self.api.count_tokens(msgs[1]))
            for i in range(len(msgs)):
                self.memory.add_log(msgs[i])
            tokens = await task
            for i in range(len(msgs)):
                msgs[i].tokens = tokens[i]
                self.logger.info(msgs[i])
            self.logger.info('Messages saved to memory')

    def save(self):
        self.logger.info('Saving memory')
        f = open('../basic_mem.txt', 'w')
        f.write(json.dumps(self.memory, cls=MemoryEncoder, indent=2))
        f.close()

    def load(self) -> None:
        self.logger.info('Loading memory...')

        try:
            f = open('../basic_mem.txt', 'r')
            dump = f.read()
            temp: AbstractMemory = json.loads(dump, cls=MemoryDecoder)
            self.logger.debug(temp.to_dict())
            self.memory = temp

        except Exception as ex:
            self.logger.error(repr(ex))
            self.logger.info('Using empty memory')
            # Currently just keeps an empty list which will overwrite unreadable json data
            # Might want to save old file under different name in case it's easily fixable
