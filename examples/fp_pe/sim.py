from hwtypes import Product, Bit
from hwtypes import TypeFamily

from .isa import Op
from .alu import ALU_fc, fp_unit_fc
from peak import Peak, family_closure, Const
from peak.family import AbstractFamily


class Inst(Product):
    op0=Op


@family_closure
def PE_fc(family: AbstractFamily):
    Data = family.BitVector[16]

    ALU = ALU_fc(family)

    fp_unit = fp_unit_fc(family)

    
    @family.assemble(locals(), globals())
    class WrappedPE(Peak):
        def __init__(self):
            self.pe : PE = PE()

        def __call__(self, inst : Const(Inst), data0 : Data, data1 : Data, fp_val : Data) -> Data:
            self.pe._set_fp(fp_val)
            return self.pe(inst, data0, data1)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.alu : ALU = ALU()
            self.fp_unit : fp_unit = fp_unit()

        def __call__(self, inst : Const(Inst), data0 : Data, data1 : Data) -> Data:
            res = self.alu(inst.op0, data0, data1, self.fp_unit)

            return res

        def _set_fp(self, fp_val : Data):
            self.fp_unit._set_fp(fp_val)

    return WrappedPE, PE
