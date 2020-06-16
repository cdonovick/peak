from hwtypes import Product, Bit, Tuple
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

    Output_T = Tuple[Data, Data]
    Output_Tc = family.get_constructor(Output_T)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.alu0 : ALU = ALU()
            self.alu1 : ALU = ALU()

        def __call__(self, inst : Inst, data0 : Data, data1 : Data) -> (Output_T, Bit):
            data1 = self.alu1(inst.op1, data0, data1)
            data0 = self.alu0(inst.op0, data0, data1)

            return Output_Tc(*[data0, data1]), Bit(0)

    return PE
