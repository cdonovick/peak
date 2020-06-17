from hwtypes import Product, Bit, Tuple
from hwtypes import TypeFamily

from .isa import Op
from .alu import ALU_fc
from peak import Peak, family_closure, Const
from peak.family import AbstractFamily

class Inst(Product, cache=True):
    op0=Op
    op1=Op
    choice=Bit

@family_closure
def PE_fc(family: AbstractFamily):
    Bit = family.Bit
    Data = family.BitVector[16]

    DataInputList = Tuple[Data, Data]
    BitInputList = Tuple[Bit, Bit]

    Output_T = Tuple[Data, Data]
    Output_Tc = family.get_constructor(Output_T)

    ALU = ALU_fc(family)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.alu0 : ALU = ALU()
            self.alu1 : ALU = ALU()

        def __call__(self, inst : Const(Inst), inputs : DataInputList, data : Data, bit_inputs : BitInputList) -> (Output_T, Bit):
            data0, bit0 = self.alu0(inst.op0, inputs[0], inputs[1], bit_inputs[1])
            data1, bit1 = self.alu1(inst.op1, inputs[0], inputs[1], bit_inputs[0])

            return Output_Tc(*[data0, data1]), bit0

    return PE
