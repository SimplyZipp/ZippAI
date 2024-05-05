# Research python discord libraries
# Research ChatGPT api
#
import sys

# No GUI, just logging to files.

# Ideas:
# Need system commands outside normal text
# How to respond to messages more human-like? Order/timing
# Track / summarize conversation history
# Configure system role
import discordclient
from testapi import TestAPI
from koboldapi import KoboldAPI
from texthandler import TextHandler
import logging
from logging import handlers
from configuration import Configuration, Fields
from memory.basic_memory import BasicMemory

import urllib.request
import socket

# Step 1: Basic functionality
#   Get bot connected to discord
#   read and respond to messages
# Step 2: Hook up ChatGPT api
#   basic question and answer queries
#   no filtering / no rule or role setting
# Step 3: Chat history


def getToken() -> str:
    token_file = open('token.txt', 'r')
    t = token_file.read()
    token_file.close()
    return t

def memory_constructor() -> BasicMemory:
    mem = BasicMemory()
    return mem

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

    handler = TextHandler(api, memory_constructor)
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
