from types import SimpleNamespace

from hwtypes.adt import Enum, Product, TaggedUnion
from hwtypes.adt_util import rebind_type

from peak import family_closure

from ..riscv import family


@family_closure(family)
def ISA_fc(family):
    Word = family.Word
    Idx = family.Idx

    class BOp(Enum):
        Add = Enum.Auto()
        Nor = Enum.Auto()

    class UOp(Enum):
        Inv = Enum.Auto()
        Mov = Enum.Auto()

    class BLayout(Product):
        op = BOp
        rs1 = Idx
        rs2 = Idx
        rd = Idx

    class ULayout(Product):
        op = UOp
        rs1 = Idx
        rd = Idx

    class Inst(TaggedUnion):
        b = BLayout
        u = ULayout

    return SimpleNamespace(**locals())
