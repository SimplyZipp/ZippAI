# Research python discord libraries
# Research ChatGPT api
#
import sys

# No GUI, just logging to files.

import discordclient
from testapi import TestAPI
from koboldapi import KoboldAPI
from discordhandlers.texthandler import TextHandler
import logging
from logging import handlers
from configuration import Configuration, Fields
from memory.factories.factories import BasicMemoryFactory


def getToken() -> str:
    token_file = open('token.txt', 'r')
    t = token_file.read()
    token_file.close()
    return t


def main() -> None:

    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s] [%(funcName)s] [%(lineno)d]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG,
                        handlers=[log_handler]
                        )
    logger = logging.getLogger(__name__)
    logger.info('*******************Log Start*******************')
    logger.info('Setting up...')

    config = Configuration()
    config.load('config.txt')
    if config.options[Fields.Owner] is None or config.options[Fields.Token] is None:
        logger.error('Token or owner is not set')

    log_handler.flush()

    #api = KoboldAPI()
    api = TestAPI()

    mem = BasicMemoryFactory()

    handler = TextHandler(api, mem)
    handler.load()

    client = discordclient.DiscordClient(response_callable=handler.respond,
                                         config=config)
    try:
        client.run(getToken())
    finally:
        handler.save()
        config.save('config.txt')
        logger.info('********************Log End********************\n')


if __name__ == '__main__':
    main()
