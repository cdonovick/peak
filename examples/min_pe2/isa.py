from hwtypes import new_instruction
from hwtypes.adt import Product, Sum, Tuple, Enum
from functools import lru_cache

@lru_cache(None)
def ISA_fc(family):
    Word = family.BitVector[8]
    Bit  = family.BitVector[1]

    class Inst(Product):
        class Opcode(Enum):
            A  = new_instruction()
            B  = new_instruction()

        operand_0 = Word
        operand_1 = Sum[Word, Tuple[Word, Bit]]

    return Word, Bit, Inst
