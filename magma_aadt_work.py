import magma as m
import hwtypes as ht

from hwtypes import BitVector, Bit
from hwtypes.adt import Product, Sum, Enum, new_instruction
from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT, AssembledADTMeta

class Inst(Product):
    a = BitVector[4]
    b = Sum[BitVector[4], Bit]
    class c(Enum):
        e0 = new_instruction()
        e1 = 1

class MAADTMeta(AssembledADTMeta, m.MagmaProtocolMeta):
    def _to_magma_(cls):
        assembler = cls.assembler_t(cls.adt_t)
        return cls.bv_type[assembler.width]

    def _from_magma_(cls, T):
        if T.undirected_t is not cls._to_magma_().undirected_t:
            raise TypeError('Cannot change or resize base magma type')

        for d in (m.Direction):
            if  T.is_oriented(d):
                return cls.unbound_t[cls.adt_t, cls.assembler_t, cls.bv_type.qualify(d)]
        raise TypeError('Something weird happened')

    def _from_magma_value_(cls, value):
        return cls(value)


class MAADT(AssembledADT, m.MagmaProtocol, metaclass=MAADTMeta):
    def _get_magma_value_(self):
        return self._value_


AInst = AssembledADT[Inst, Assembler,  m.Bits]
MAInst = MAADT[Inst, Assembler, m.Bits]

@m.syntax.sequential.sequential
class Foo:

    def __call__(self, inst: MAInst) -> m.Bits[2]:
        #return ~inst0
        if inst.b[Bit].match:
            lsb = m.Bits[1](0)
        else:
            lsb = m.Bits[1](1)

        if inst.c == Inst.c.e0:
            msb = m.Bits[1](0)
        else:
            msb = m.Bits[1](1)
        return lsb.concat(msb)

m.compile("Foo", Foo)
