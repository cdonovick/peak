from hwtypes.adt import Product, Sum, Tuple, Enum
from peak import family_closure
from types import SimpleNamespace


class Op(Enum):
    A = 1
    B = 2

@family_closure
def ISA_fc(family):
    Word = family.BitVector[8]
    Bit  = family.BitVector[1]

    BitOp = Tuple[Op, Bit]

    ArithOp = Tuple[Op, Word]

    Inst = Sum[BitOp, ArithOp]

    return SimpleNamespace(**locals(), Op=Op)
