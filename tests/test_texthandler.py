import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase
from testapi import TestAPI
from memory.factories.factories import NoMemoryFactory, BasicMemoryFactory
from discordhandlers.abstracthandler import BasicMessage
from discordhandlers.texthandler import TextHandler


class MessageResponses(IsolatedAsyncioTestCase):

    api = TestAPI()  # These two don't keep state
    mem = NoMemoryFactory()
    handler: TextHandler | None = None  # This one does

    def setUp(self):
        self.handler = TextHandler(self.api, {}, default_factory=self.mem)
        self.api.set_sleep_time(0.1)
        self.api.blank = False

    async def asyncTearDown(self) -> None:
        # Wait for async api call to finish
        async with self.handler.lock(0):
            pass

    async def test_basic_response(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=0))
        self.assertEqual(res, 'structured: test')

    async def test_basic_response_2(self):
        res = await self.handler.respond(BasicMessage('test hello', user='me', unique_id=0))
        self.assertEqual(res, 'structured: test hello')

    async def test_empty_response(self):
        res = await self.handler.respond(BasicMessage('', user='me', unique_id=0))
        self.assertEqual(res, 'structured: ')

    async def test_empty_response2(self):
        res = await self.handler.respond(BasicMessage(' ', user='me', unique_id=0))
        self.assertEqual(res, 'structured:  ')

    async def test_basic_response_multiple(self):
        self.api.set_sleep_time(0.5)
        res = await asyncio.gather(self.handler.respond(BasicMessage('test', user='me', unique_id=0)),
                                   self.handler.respond(BasicMessage('test2', user='me', unique_id=0)))
        self.assertEqual(res[0], 'structured: test')
        self.assertEqual(res[1], 'structured: test2')

    async def test_no_response(self):
        self.api.blank = True
        res = await self.handler.respond(BasicMessage('', user='me', unique_id=0))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage(' ', user='me', unique_id=0))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage('\t', user='me', unique_id=0))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage('\r\n', user='me', unique_id=0))
        self.assertEqual(res, '[No response]')

    async def test_value_error(self):
        self.api.trigger_value_error()
        res = await self.handler.respond(BasicMessage('Test message', user='me', unique_id=0))
        self.assertEqual(res, '[Internal error encountered during processing]')

    async def test_runtime_error(self):
        self.api.trigger_runtime_error()
        res = await self.handler.respond(BasicMessage('Test message', user='me', unique_id=0))
        self.assertEqual(res, '[RuntimeError message]')


class UsingMemoryTests(IsolatedAsyncioTestCase):

    api = TestAPI()  # These two don't keep state
    mem = BasicMemoryFactory()
    handler: TextHandler | None = None  # This one does

    def setUp(self):
        self.handler = TextHandler(self.api, {}, default_factory=self.mem)
        self.api.set_sleep_time(0.1)
        self.api.blank = False

    async def asyncTearDown(self) -> None:
        # Wait for async api call to finish
        for memid in self.handler.memories:
            async with self.handler.lock(int(memid)):
                pass

    async def test_single_message(self):
        # Technically testing BasicMemory, but useful to determine if the handler is actually using the memory
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=0))
        self.assertEqual(2, len(self.handler.memory(0).log))
        self.assertEqual('test', self.handler.memory(0).log[0].content)
        self.assertEqual('structured: test', self.handler.memory(0).log[1].content)

    async def test_two_message(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=0))
        res = await self.handler.respond(BasicMessage('test2', user='me', unique_id=0))
        self.assertEqual(4, len(self.handler.memory(0).log))
        self.assertEqual('test', self.handler.memory(0).log[0].content)
        self.assertEqual('structured: test', self.handler.memory(0).log[1].content)
        self.assertEqual('test2', self.handler.memory(0).log[2].content)
        self.assertEqual('structured: test2', self.handler.memory(0).log[3].content)

    async def test_two_memories_ids(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=245))
        res = await self.handler.respond(BasicMessage('test2', user='me', unique_id=14793028534287569))
        self.assertEqual(2, len(self.handler.memories.keys()))
        self.assertTrue('245' in self.handler.memories)
        self.assertTrue('14793028534287569' in self.handler.memories)

    async def test_two_memories(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=0))
        res = await self.handler.respond(BasicMessage('test2', user='me', unique_id=1))
        self.assertEqual(2, len(self.handler.memory(0).log))
        self.assertEqual('test', self.handler.memory(0).log[0].content)
        self.assertEqual('structured: test', self.handler.memory(0).log[1].content)
        self.assertEqual('test2', self.handler.memory(1).log[0].content)
        self.assertEqual('structured: test2', self.handler.memory(1).log[1].content)

    async def test_two_memories_many_messages(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=346135))
        res = await self.handler.respond(BasicMessage('test2', user='me', unique_id=9))
        res = await self.handler.respond(BasicMessage('hello', user='me', unique_id=346135))
        res = await self.handler.respond(BasicMessage('hi', user='me', unique_id=9))
        res = await self.handler.respond(BasicMessage('wait', user='me', unique_id=9))
        self.assertEqual(4, len(self.handler.memory(346135).log))
        self.assertEqual(6, len(self.handler.memory(9).log))
        self.assertEqual('test', self.handler.memory(346135).log[0].content)
        self.assertEqual('hello', self.handler.memory(346135).log[2].content)
        self.assertEqual('test2', self.handler.memory(9).log[0].content)
        self.assertEqual('hi', self.handler.memory(9).log[2].content)
        self.assertEqual('wait', self.handler.memory(9).log[4].content)


if __name__ == '__main__':
    unittest.main()
