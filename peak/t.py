from bit_vector import BitVector as BV
from enum import Enum
from typing import NamedTuple, Union

__all__ =  ['Bits', 'is_bits']
__all__ += ['Enum', 'is_enum']
__all__ += ['Tuple', 'is_tuple']
__all__ += ['Union', 'is_union', 'match']

def Bits(n):
    class _Bits(BV):
        def __init__(self, i):
            super().__init__(i,n)
    return _Bits

Tuple = NamedTuple

def match(value, case):
    for klass, func in case.items():
       if type(value) == klass:
            func(value)

def is_bits(t):
    return issubclass(t,BV)

def is_enum(t):
    return issubclass(t,Enum)

def is_union(t):
    return hasattr(t,'__origin__') and t.__origin__ is Union

def is_tuple(t):
    return not is_union(t) and not is_bits(t) and not is_enum(t)
