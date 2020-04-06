from hwtypes import new_instruction
from hwtypes.adt import Product, Sum, Tuple, Enum
from functools import lru_cache
from peak import Const

@lru_cache(None)
def ISA_fc(family):
    Word = family.BitVector[8]
    Bit  = family.BitVector[1]

    Operand0T = Word
    Operand1T = Sum[Word, Tuple[Word, Bit]]
    class Inst(Product):
        class Opcode(Enum):
            A  = 1
            B  = 2
        offset = Word
    return Inst, Operand0T, Operand1T, Word, Tuple[Word, Bit]
