from typing import Optional
from magma.protocol_type import MagmaProtocolMeta, MagmaProtocol
from magma.t import Type, Direction


import pytest

from hwtypes import Bit, SMTBit, SMTBitVector, BitVector, Enum

import fault
import magma as m
from peak.magma_vector import MagmaBit, MagmaBitVector
import itertools


from peak import Peak, family_closure, Const
from peak.assembler import Assembler, AssembledADT
from peak.assembler2.assembler import Assembler as Assembler2
from peak.assembler2.assembled_adt import AssembledADT as AssembledADT2
from peak.rtl_utils import wrap_with_disassembler
from peak import family
from peak import name_outputs

from examples.demo_pes.pe6 import PE_fc
from examples.demo_pes.pe6.sim import Inst

class SimpleMagmaProtocolMeta(MagmaProtocolMeta):
    _CACHE = {}

#     def __new__(cls, name, bases, namespace, info=(None, None), **kwargs):
#         pass
#     def __getitem__(cls, direction: m.Direction) -> 'MagmaBitMeta':

    @property
    def is_directed(cls) ->  'Bool':
        pass

    @property
    def undirected_t(cls) -> 'MagmaBitMeta':
        pass

#     def _to_magma_(cls): 
#         pass

#     def _qualify_magma_(cls, d): 
#         pass


#     def _flip_magma_(cls): 
#         pass

#     def _from_magma_value_(cls, value):
#         pass


    def _to_magma_(cls):
        return cls.T

    def _qualify_magma_(cls, direction: Direction):
        return cls[cls.T.qualify(direction)]

    def _flip_magma_(cls):
        return cls[cls.T.flip()]

    def _from_magma_value_(cls, val: Type):
        return cls(val)

    def __getitem__(cls, T):
        try:
            base = cls.base
        except AttributeError:
            base = cls
        dct = {"T": T, "base": base}
        derived = type(cls)(f"{base.__name__}[{T}]", (cls,), dct)
        return SimpleMagmaProtocolMeta._CACHE.setdefault(T, derived)

    def __repr__(cls):
        return str(cls)

    def __str__(cls):
        return cls.__name__


class SimpleMagmaProtocol(MagmaProtocol, metaclass=SimpleMagmaProtocolMeta):
    def __init__(self, val: Optional[Type] = None):
        if val is None:
            val = self.T()
        self._val = val



    @staticmethod
    def get_family():
        return

#     def __init__(self, *args, **kwargs):
#         return
#         pass
#         self._value=m.Bit(*args, **kwargs)

    def __repr__(self):
        return
        pass
        return self._value.__repr__()

    @property
    def value(self):
        return
        pass
        return self._value

    # @bit_cast
    def __eq__(self, other : 'MagmaBit') -> 'MagmaBit':
        return
        pass
        return type(self)(self.value.__eq__(other.value))

    # @bit_cast
    def __ne__(self, other : 'MagmaBit') -> 'MagmaBit':
        return
        return type(self)(self.value.__ne__(other.value))

    def __invert__(self) -> 'MagmaBit':
        return
        return type(self)(self.value.__invert__())

    # @bit_cast
    def __and__(self, other : 'MagmaBit') -> 'MagmaBit':
        return
        return type(self)(self.value.__and__(other.value))

    # @bit_cast
    def __or__(self, other : 'MagmaBit') -> 'MagmaBit':
        return
        return type(self)(self.value.__or__(other.value))

    # @bit_cast
    def __xor__(self, other : 'MagmaBit') -> 'MagmaBit':
        return
        return type(self)(self.value.__xor__(other.value))

    def ite(self, t_branch, f_branch):
        return
        return type(self)(self.value.ite(t_branch, f_branch))

#         def _ite(select, t_branch, f_branch):
#             return smt.Ite(select.value, t_branch.value, f_branch.value)
#         return build_ite(_ite, self, t_branch, f_branch)

    def __bool__(self):
        return
        raise TypeError('MagmaBit cannot be converted to bool')

        






    def _get_magma_value_(self):
        return self._val

    def non_standard_operation(self):
        v0 = self._val << 2
        v1 = bits(self._val[0], len(self.T)) << 1
        return SimpleMagmaProtocol(v0 | v1 | bits(self._val[0], len(self.T)))


def test_foo():
    class bitfoo(m.Circuit):
        io = m.IO(
            I=m.In( SimpleMagmaProtocol[m.Bit]), 
            O=m.Out(SimpleMagmaProtocol[m.Bit])
        )
#          io = m.IO(
#              I=m.In( MagmaBit ), 
#              O=m.Out(MagmaBit )
#          )
        
        
