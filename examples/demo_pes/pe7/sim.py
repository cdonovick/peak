from hwtypes import Product, Bit, Tuple
from hwtypes import TypeFamily

from .isa import Op
from .alu import ALU_fc
from peak import Peak, assemble, family_closure

class Inst(Product):
    op0=Op
    op1=Op
    choice=Bit

@family_closure
def PE_fc(family : TypeFamily):
    Bit = family.Bit
    Data = family.BitVector[16]
    inputsType = Tuple[(Data, Data)]

    ALU = ALU_fc(family)

    @assemble(family, locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.alu0 : ALU = ALU()
            self.alu1 : ALU = ALU()

        def __call__(self, inst : Inst, inputs: inputsType) -> Data:
            data1 = self.alu1(inst.op1, inputs[0], inputs[1])
            data0 = self.alu0(inst.op0, inputs[0], inputs[1])

            if inst.choice:
                return data1
            else:
                return data0

    return PE
