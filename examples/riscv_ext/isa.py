from types import SimpleNamespace

from hwtypes.adt import Enum, Product, TaggedUnion, Sum
from hwtypes.adt_util import rebind_type

from peak import family_closure

from . import family
from ..riscv import isa


@family_closure(family)
def ISA_fc(family):
    ns = isa.ISA_fc(family)

    class E(Product):
        rd = ns.Idx
        rs = ns.Idx

    class BitInst(Enum):
        POPCNT = Enum.Auto()
        CNTLZ = Enum.Auto()
        CNTTZ = Enum.Auto()


    class Ext(Product):
        data = E
        tag = BitInst



    ns.E = E
    ns.BitInst = BitInst
    ns.Ext = Ext
    # replace Inst
    ns.Inst = Sum[ns.OP, ns.OP_IMM, ns.LUI, ns.AUIPC, ns.JAL, ns.JALR, ns.Branch, ns.Load, ns.Store, Ext]

    return ns
