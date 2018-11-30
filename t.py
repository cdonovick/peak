from bit_vector import BitVector as BV
from enum import Enum
from typing import NamedTuple, Union

__all__ = ['Bits', 'Enum', 'Struct', 'Union', 'match']

def Bits(n):
    class _Bits(BV):
        def __init__(self, i):
            super().__init__(i,n)
    return _Bits

Struct = NamedTuple

def match(value, case):
    for klass, func in case.items():
       if type(value) == klass:
            func(value)
