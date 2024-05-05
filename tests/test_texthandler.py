import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase
from testapi import TestAPI
from memory.no_memory import NoMemory
from discordclient import BasicMessage
from texthandler import TextHandler


class MessageResponses(IsolatedAsyncioTestCase):

    api = TestAPI()  # These two don't keep state
    mem = NoMemory()
    handler: TextHandler | None = None  # This one does

    def setUp(self):
        self.handler = TextHandler(self.api, self.mem)
        self.api.set_sleep_time(0.1)
        self.api.blank = False

    async def asyncTearDown(self) -> None:
        # Wait for async api call to finish
        async with self.handler.mem_lock:
            pass

    async def test_basic_response(self):
        res = await self.handler.respond(BasicMessage('test', user='me', unique_id=None))
        self.assertEqual(res, 'structured: test')

    async def test_basic_response_2(self):
        res = await self.handler.respond(BasicMessage('test hello', user='me', unique_id=None))
        self.assertEqual(res, 'structured: test hello')

    async def test_empty_response(self):
        res = await self.handler.respond(BasicMessage('', user='me', unique_id=None))
        self.assertEqual(res, 'structured: ')

    async def test_empty_response2(self):
        res = await self.handler.respond(BasicMessage(' ', user='me', unique_id=None))
        self.assertEqual(res, 'structured:  ')

    async def test_basic_response_multiple(self):
        self.api.set_sleep_time(0.5)
        res = await asyncio.gather(self.handler.respond(BasicMessage('test', user='me', unique_id=None)),
                                   self.handler.respond(BasicMessage('test2', user='me', unique_id=None)))
        self.assertEqual(res[0], 'structured: test')
        self.assertEqual(res[1], 'structured: test2')

    async def test_no_response(self):
        self.api.blank = True
        res = await self.handler.respond(BasicMessage('', user='me', unique_id=None))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage(' ', user='me', unique_id=None))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage('\t', user='me', unique_id=None))
        self.assertEqual(res, '[No response]')
        res = await self.handler.respond(BasicMessage('\r\n', user='me', unique_id=None))
        self.assertEqual(res, '[No response]')

    async def test_value_error(self):
        self.api.trigger_value_error()
        res = await self.handler.respond(BasicMessage('Test message', user='me', unique_id=None))
        self.assertEqual(res, '[Internal error encountered during processing]')

    async def test_runtime_error(self):
        self.api.trigger_runtime_error()
        res = await self.handler.respond(BasicMessage('Test message', user='me', unique_id=None))
        self.assertEqual(res, '[RuntimeError message]')


if __name__ == '__main__':
    unittest.main()
