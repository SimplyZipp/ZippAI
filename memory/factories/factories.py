import logging
import typing
from memory.factories.memoryfactory import MemoryFactory
from memory.no_memory import NoMemory
from memory.basic_memory import BasicMemory


class NoMemoryFactory(MemoryFactory):

    def make_memory(self) -> NoMemory:
        self.logger.debug('Creating new NoMemory')
        return NoMemory()


class BasicMemoryFactory(MemoryFactory):

    def make_memory(self) -> BasicMemory:
        self.logger.debug('Creating new BasicMemory')
        return BasicMemory()
