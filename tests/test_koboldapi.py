import unittest
from unittest import IsolatedAsyncioTestCase
import asyncio
import json

import httpx

import koboldapi
from koboldapi import KoboldAPI
import koboldai
from memory.memory import Message, Role

import respx
from httpx import Response


def gen_side_effect(request: httpx.Request, route):
    content = json.loads(request.content)
    dct = {'results': [{'text': f'Gen:{content["prompt"]}'}]}
    return Response(200, text=json.dumps(dct))


def tokencount_side_effect(request: httpx.Request, route):
    # Set the "tokencount" value to the number of words
    cont: dict[str, str] = json.loads(request.content)
    length = len(cont['prompt'].split(' '))
    result = {'value': length, 'ids': [i for i in range(length)]}
    return Response(200, content=json.dumps(result))


class KoboldAITests(IsolatedAsyncioTestCase):

    base_url = 'http://localhost:5001'
    client: koboldai.Client

    def setUp(self) -> None:
        self.client = koboldai.Client(self.base_url)

    @respx.mock(base_url=base_url)
    async def test_get_api(self, respx_mock):
        # Setup response interceptions
        respx_mock.get(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH).mock(
            return_value=Response(200, text='{"value": 2048}'))
        respx_mock.get(koboldai.Client.ROUTE_MODEL).mock(
            return_value=Response(200, text='{"result": "modelv1"}'))

        # Call client and check results
        dct = await self.client.get_api(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH)
        self.assertEqual(dct, {'value': 2048})
        dct = await self.client.get_api(koboldai.Client.ROUTE_MODEL)
        self.assertEqual(dct, {'result': 'modelv1'})

    @respx.mock(base_url=base_url)
    async def test_get_api_req_err(self, respx_mock):
        # Setup error interception
        respx_mock.get(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH).mock(
            side_effect=httpx.RequestError
        )

        # Test that call throws correct error
        with self.assertRaises(RuntimeError):
            await self.client.get_api(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH)

    @respx.mock(base_url=base_url)
    async def test_get_api_stat_err(self, respx_mock):
        # Setup not OK responses
        respx_mock.get(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH).mock(
            return_value=Response(404)
        )
        respx_mock.get(koboldai.Client.ROUTE_MODEL).mock(
            return_value=Response(503)
        )

        # Test that call throws correct error
        with self.assertRaises(RuntimeError):
            await self.client.get_api(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH)
        with self.assertRaises(RuntimeError):
            await self.client.get_api(koboldai.Client.ROUTE_MODEL)


    @respx.mock(base_url=base_url)
    async def test_post_api(self, respx_mock):
        # Create some fake results
        gen_result = {'results': [{'text': 'generated output'}]}

        # Setup post interceptions
        respx_mock.post(koboldai.Client.ROUTE_GENERATE).mock(
            return_value=Response(200, text=json.dumps(gen_result)))
        respx_mock.post(koboldai.Client.ROUTE_TOKENCOUNT).mock(
            side_effect=tokencount_side_effect)

        # Call client and check result
        dct = await self.client.post_api(koboldai.Client.ROUTE_GENERATE, {})
        self.assertEqual(dct, gen_result)
        dct = await self.client.post_api(koboldai.Client.ROUTE_TOKENCOUNT, {'prompt': 'random text two'})
        self.assertEqual(dct, {'value': 3, 'ids': [i for i in range(3)]})

    @respx.mock(base_url=base_url)
    async def test_post_api_req_err(self, respx_mock):
        # Setup error interception
        respx_mock.post(koboldai.Client.ROUTE_GENERATE).mock(
            side_effect=httpx.RequestError
        )

        # Test that call throws correct error
        with self.assertRaises(RuntimeError):
            await self.client.post_api(koboldai.Client.ROUTE_GENERATE, {})

    @respx.mock(base_url=base_url)
    async def test_post_api_stat_err(self, respx_mock):
        # Setup not OK response
        respx_mock.post(koboldai.Client.ROUTE_GENERATE).mock(
            return_value=Response(503)
        )

        # Test that call throws correct error
        with self.assertRaises(RuntimeError):
            await self.client.post_api(koboldai.Client.ROUTE_GENERATE, {})

    @respx.mock(base_url=base_url)
    async def test_max_context_length(self, respx_mock):
        respx_mock.get(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH).mock(
            return_value=Response(200, text='{"value":2048}')
        )
        res = await self.client.max_context_length()
        self.assertEqual(2048, res)

        respx_mock.get(koboldai.Client.ROUTE_MAX_CONTEXT_LENGTH).mock(
            return_value=Response(200, text='{"value":4096}')
        )
        res = await self.client.max_context_length()
        self.assertEqual(4096, res)

    @respx.mock(base_url=base_url)
    async def test_max_length(self, respx_mock):
        respx_mock.get(koboldai.Client.ROUTE_MAX_LENGTH).mock(
            return_value=Response(200, text='{"value":512}')
        )
        res = await self.client.max_length()
        self.assertEqual(512, res)

        respx_mock.get(koboldai.Client.ROUTE_MAX_LENGTH).mock(
            return_value=Response(200, text='{"value":80}')
        )
        res = await self.client.max_length()
        self.assertEqual(80, res)



    @respx.mock(base_url=base_url)
    async def test_generate(self, respx_mock):
        respx_mock.post(koboldai.Client.ROUTE_GENERATE).mock(
            side_effect=gen_side_effect
        )
        generated = await self.client.generate('test str')
        self.assertEqual('Gen:test str', generated)

        generated = await self.client.generate('\n Hello world')
        self.assertEqual('Gen:\n Hello world', generated)

    @respx.mock(base_url=base_url)
    async def test_tokencount(self, respx_mock):
        respx_mock.post(koboldai.Client.ROUTE_TOKENCOUNT).mock(
            side_effect=tokencount_side_effect)

        res = await self.client.tokencount('random text two')
        self.assertEqual(3, res)
        res = await self.client.tokencount('hi hi hihi hi')
        self.assertEqual(4, res)


class KoboldCppAPITests(IsolatedAsyncioTestCase):

    base_url = 'http://localhost:5001'
    api: koboldapi.KoboldAPI

    api_mock = respx.mock(base_url='http://localhost:5001', assert_all_called=False)

    api_mock.post(koboldai.Client.ROUTE_TOKENCOUNT).mock(
        side_effect=tokencount_side_effect
    )

    # Dictionary to store data passed through http
    generate_params = {}

    def gen_side_effect(self, request: httpx.Request, route):
        content = json.loads(request.content)
        self.generate_params = content.copy()
        dct = {'results': [{'text': 'Generated text'}]}
        return Response(200, text=json.dumps(dct))

    def setUp(self) -> None:
        self.api = koboldapi.KoboldAPI()

        # Reset dictionary for every test
        self.generate_params = {}
        self.api_mock.post(koboldai.Client.ROUTE_GENERATE).mock(
            side_effect=self.gen_side_effect
        )

    async def test_get_response(self):
        with self.api_mock:
            response = await self.api.get_response('test', [])
            self.assertEqual('test', self.generate_params['prompt'])
            self.assertEqual([], self.generate_params['stop_sequence'])
            self.generate_params = {}
            response = await self.api.get_response('test', None)
            self.assertEqual([], self.generate_params['stop_sequence'])

    async def test_get_response_prompt(self):
        with self.api_mock:
            response = await self.api.get_response('The quick brown fox jumped over the lazy dog.\n', [])
            # Test that the prompt is correctly received
            self.assertEqual('The quick brown fox jumped over the lazy dog.\n', self.generate_params['prompt'])
            # Test that the response is returned from generate
            self.assertEqual('Generated text', response)

    async def test_get_response_stop_1(self):
        with self.api_mock:
            response = await self.api.get_response('test', ['test:'])
            self.assertEqual(['test:'], self.generate_params['stop_sequence'])

    async def test_get_response_stop_2(self):
        with self.api_mock:
            response = await self.api.get_response('test', ['test:', 'User: '])
            self.assertEqual(['test:', 'User: '], self.generate_params['stop_sequence'])

    async def test_get_response_structured(self):
        with self.api_mock:
            response = await self.api.get_response_structured('test message', None, None)
            pos = self.generate_params['prompt'].find('test message')
            self.assertTrue(pos > -1)

    async def test_get_response_structured_history(self):
        with self.api_mock:
            messages = ['past message', 'past response']
            order = [1, 0]
            # Make history in proper order (same order as messages list above)
            history = [
                Message(role=Role(index % 2), content=messages[index], tokens=2) for index in range(len(messages))
            ]
            response = await self.api.get_response_structured('test message', history, order)
            pos = 0

            # Look for history in the prompt in proper order (none should be cut off rn)
            for index in reversed(order):
                pos = self.generate_params['prompt'].find(messages[index], pos)
                self.assertTrue(pos > -1)
            # Look for the actual message
            pos = self.generate_params['prompt'].find('test message', pos)
            self.assertTrue(pos > -1)

    async def test_get_response_structured_history_2(self):
        with self.api_mock:
            messages = ['past message',
                        'past response',
                        'more relevant message',
                        'more relevant response',
                        'less relevant message',
                        'less relevant response']
            order = [3, 2, 1, 0, 5, 4]
            # Make history in proper order (same order as messages list above)
            history = [
                Message(role=Role(index % 2), content=messages[index], tokens=2) for index in range(len(messages))
            ]
            response = await self.api.get_response_structured('test message', history, order)
            pos = 0

            # Look for history in the prompt in proper order (none should be cut off rn)
            for index in reversed(order):
                pos = self.generate_params['prompt'].find(messages[index], pos)
                self.assertTrue(pos > -1)
            # Look for the actual message
            pos = self.generate_params['prompt'].find('test message', pos)
            self.assertTrue(pos > -1)

    async def test_get_response_structured_history_many_tokens(self):
        with self.api_mock:
            messages = ['past message', 'past response']
            order = [1, 0]
            # Make history in proper order (same order as messages list above)
            history = [
                Message(role=Role(index % 2), content=messages[index], tokens=1024) for index in range(len(messages))
            ]
            response = await self.api.get_response_structured('test message', history, order)
            pos = 0

            # Look for history in the prompt in proper order (none should be cut off rn)
            # Start at 2, step down to 1
            for index in order[2:1:-1]:
                pos = self.generate_params['prompt'].find(messages[index], pos)
                self.assertTrue(pos > -1)
            # Look for the actual message
            pos = self.generate_params['prompt'].find('test message', pos)
            self.assertTrue(pos > -1)

    async def test_get_response_structured_history_max_tokens(self):
        with self.api_mock:
            messages = ['past message', 'past response']
            order = [1, 0]
            # Make history in proper order (same order as messages list above)
            history = [
                Message(role=Role(index % 2), content=messages[index], tokens=2000) for index in range(len(messages))
            ]
            response = await self.api.get_response_structured('test message', history, order)
            pos = 0

            # Look for the actual message
            pos = self.generate_params['prompt'].find('test message', pos)
            self.assertTrue(pos > -1)

    async def test_get_response_structured_history_no_tokens(self):
        with self.api_mock:
            messages = ['past message', 'past response']
            order = [1, 0]
            # Make history in proper order (same order as messages list above)
            # One of them has 0 tokens
            history = [
                Message(role=Role(index % 2), content=messages[index], tokens=index) for index in range(len(messages))
            ]
            with self.assertRaises(ValueError):
                response = await self.api.get_response_structured('test message', history, order)


if __name__ == '__main__':
    unittest.main()
