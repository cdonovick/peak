from functools import lru_cache

from peak import family_closure
from hwtypes import Enum, Product
from types import SimpleNamespace

@lru_cache(None)
def gen_isa(width):
    class OP(Enum):
        imm = 1
        Add = 2
        Mux = 6

    @family_closure
    def isa_fc(family):
        Bit = family.Bit
        Data = family.BitVector[width]
        SData = family.Signed[width]
        LUT_t = family.BitVector[8]
        IDX_t = family.BitVector[3]

        class AluInst(Product):
            op = OP
            imm = family.BitVector[width]

        class Inst(Product):
            alu_inst = AluInst
            lut = LUT_t
        return SimpleNamespace(**locals())
    return isa_fc
