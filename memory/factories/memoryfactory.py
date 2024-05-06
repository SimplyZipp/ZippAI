import logging
import typing
from memory.memory import AbstractMemory


class MemoryFactory:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def make_memory(self) -> AbstractMemory:
        raise NotImplemented('MemoryFactory should not be directly created')
