from hwtypes import Product, Bit
from hwtypes import TypeFamily

from .isa import Op
from .alu import ALU_fc
from peak import Peak, family_closure
from peak.family import AbstractFamily


class Inst(Product):
    op0=Op
    op1=Op
    choice=Bit

@family_closure
def PE_fc(family: AbstractFamily):
    Bit = family.Bit
    Data = family.BitVector[16]

    ALU = ALU_fc(family)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.alu0 : ALU = ALU()
            self.alu1 : ALU = ALU()

        def __call__(self, inst : Inst, data0 : Data, data1 : Data) -> Data:
            data1 = self.alu1(inst.op1, data0, data1)
            data0 = self.alu0(inst.op0, data0, data1)

            if inst.choice:
                return data1
            else:
                return data0

    return PE
