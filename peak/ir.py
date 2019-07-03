from collections import namedtuple
import typing as tp

class IR:
    def __init__(self):
        #Stores a list of instructions (name : family_closure)
        self.instructions = {}
    def add_instruction(self, name : str, semantics :  tp.Callable):
        if name in self.instructions:
            raise ValueError(f"{name} is already an existing instruction")
        self.instructions[name] = semantics
