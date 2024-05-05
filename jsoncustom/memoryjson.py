from memory.memory import AbstractMemory
from memory.basic_memory import BasicMemory
import json
import typing
from typing import Any


class MemoryEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, AbstractMemory):
            # Convert memory objects to a dict (as implemented by the class)
            return o.to_dict()

        return super().default(o)


class MemoryDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        # Converts the '__class__' attribute from memory classes to their actual class.
        self.memory_type_mapping = {
            'BasicMemory': BasicMemory
        }

        super().__init__(object_hook=self.my_obj_hook, *args, **kwargs)

    def my_obj_hook(self, dct: dict):
        # Non custom objects won't have '__class__'
        if dct.get('__class__') is None:
            return dct
        class_type = self.memory_type_mapping[dct.get('__class__')]
        if issubclass(class_type, AbstractMemory):  # Probably don't even need this if statement
            return class_type.from_dict(dct)  # Return an object from its dict representation
        return dct
