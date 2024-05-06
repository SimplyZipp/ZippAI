import httpx
import json
import logging


class Client:

    ROUTE_MAX_CONTEXT_LENGTH = '/api/v1/config/max_context_length'
    ROUTE_MAX_LENGTH = '/api/v1/config/max_length'
    ROUTE_GENERATE = '/api/v1/generate'
    ROUTE_VERSION = '/api/v1/info/version'
    ROUTE_MODEL = '/api/v1/model'
    ROUTE_TOKENCOUNT = '/api/extra/tokencount'

    def __init__(self, url: str):
        self.http_client = httpx.AsyncClient(base_url=url)  # For better testing, don't initialize client here
        self.logger = logging.getLogger(__name__)

    async def get_api(self, path: str) -> dict:
        try:
            response: httpx.Response = await self.http_client.get(path)
            response.raise_for_status()
        except httpx.RequestError as ex:
            # Probably means there is no connection to the http server. Dropped or offline.
            self.logger.error(repr(ex))
            raise RuntimeError(f'Error getting HTTP response: {ex}')
        except httpx.HTTPStatusError as ex:
            self.logger.error(repr(ex))
            raise RuntimeError(f'Error {ex.response.status_code}. The server is likely busy')

        res_dict = json.loads(response.content)
        return res_dict

    async def post_api(self, path: str, body: dict) -> dict:
        content = json.dumps(body)

        try:
            response = await self.http_client.post(path, content=content, timeout=20.0)
            response.raise_for_status()
        except httpx.RequestError as ex:
            self.logger.error(repr(ex))
            raise RuntimeError(f'Error getting HTTP response: {ex}')
        except httpx.HTTPStatusError as ex:
            self.logger.error(repr(ex))
            raise RuntimeError(f'Error {ex.response.status_code}. The server is likely busy')

        return json.loads(response.content)

    async def max_context_length(self) -> int:
        response = await self.get_api(self.ROUTE_MAX_CONTEXT_LENGTH)
        return response['value']

    async def max_length(self):
        response = await self.get_api(self.ROUTE_MAX_LENGTH)
        return response['value']

    async def generate(self, prompt: str, **parameters):
        """

        :param prompt:
        :param parameters: Parameters are keyword arguments. The following are supported:

        max_context_length (integer):
                Maximum number of tokens to send to the model.

        max_length	    (integer)
                minimum: 1
                Number of tokens to generate.

        rep_pen	        (number)
                minimum: 1
                Base repetition penalty value.

        rep_pen_range	(integer)
                minimum: 0
                Repetition penalty range.

        sampler_order	(array of integers)
                minItems: 6
                Sampler order to be used. If N is the length of this array, then N must be greater than or equal to 6 and the array must be a permutation of the first N non-negative integers.

        sampler_seed	(integer)
                maximum: 999999
                minimum: 1
                RNG seed to use for sampling. If not specified, the global RNG will be used.

        stop_sequence	(array of strings)
                An array of string sequences where the API will stop generating further tokens. The returned text WILL contain the stop sequence.

        temperature	    (number)
                exclusiveMinimum: 0
                Temperature value.

        tfs	            (number)
                maximum: 1
                minimum: 0
                Tail free sampling value.

        top_a	        (number)
                minimum: 0
                Top-a sampling value.

        top_k	(integer)
                minimum: 0
                Top-k sampling value.

        top_p	(number)
                maximum: 1
                minimum: 0
                Top-p sampling value.

        min_p	(number)
                maximum: 1
                minimum: 0
                Min-p sampling value.

        typical	(number)
                maximum: 1
                minimum: 0
                Typical sampling value.

        use_default_badwordsids	(boolean)
                default: false
                If true, prevents the EOS token from being generated (Ban EOS). For unbantokens, set this to false.

        dynatemp_range	(number)
                default: 0
                exclusiveMinimum: 0
                If greater than 0, uses dynamic temperature. Dynamic temperature range will be between Temp+Range and
                Temp-Range. If less or equal to 0 , uses static temperature.

        smoothing_factor	(number)
                default: 0
                exclusiveMinimum: 0
                Modifies temperature behavior. If greater than 0 uses smoothing factor.

        dynatemp_exponent	(number)
                default: 1
                Exponent used in dynatemp.

        mirostat	(number)
                minimum: 0
                maximum: 2
                KoboldCpp ONLY. Sets the mirostat mode, 0=disabled, 1=mirostat_v1, 2=mirostat_v2

        mirostat_tau	(number)
                exclusiveMinimum: 0
                KoboldCpp ONLY. Mirostat tau value.

        mirostat_eta	(number)
                exclusiveMinimum: 0
                KoboldCpp ONLY. Mirostat eta value.

        genkey	(string)
                KoboldCpp ONLY. A unique genkey set by the user. When checking a polled-streaming request, use this key
                to be able to fetch pending text even if multiuser is enabled.

        grammar	(string)
                KoboldCpp ONLY. A string containing the GBNF grammar to use.

        grammar_retain_state	(boolean)
                default: false
                KoboldCpp ONLY. If true, retains the previous generation's grammar state,
                otherwise it is reset on new generation.

        memory	(string)
                KoboldCpp ONLY. If set, forcefully appends this string to the beginning of any submitted prompt text.
                If resulting context exceeds the limit, forcefully overwrites text from the beginning of the main
                prompt until it can fit. Useful to guarantee full memory insertion even when you cannot
                determine exact token count.

        images	(array of strings)
                KoboldCpp ONLY. If set, takes an array of base64 encoded strings,
                each one representing an image to be processed.
        :return:
        """
        self.logger.info('Initiating generate call')
        params = {
            'prompt': prompt,
            **parameters
        }
        output = await self.post_api(self.ROUTE_GENERATE, params)
        return output['results'][0]['text']

    async def version(self) -> str:
        response = await self.get_api(self.ROUTE_VERSION)
        return response['result']

    async def model(self) -> str:
        response = await self.get_api(self.ROUTE_MODEL)
        return response['result']

    async def tokencount(self, prompt: str) -> int:
        response = await self.post_api(self.ROUTE_TOKENCOUNT, {'prompt': prompt})
        return response['value']


if __name__ == '__main__':
    cli = Client('http://localhost:5001')
    print(cli.generate('Where does "Hello world" come from?'))

