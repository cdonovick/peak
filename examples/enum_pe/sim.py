from peak import Peak, family_closure, name_outputs, assemble
import magma as m

from .alu import ALU_fc
from .isa import Inst_fc
from hwtypes import Tuple

@family_closure
def PE_fc(family):

    Data = family.BitVector[16]
    Out_Data = family.BitVector[16]
    Bit = family.Bit
    
    ALU = ALU_fc(family)
    Inst = Inst_fc(family)
    DataInputList = Tuple[(Data for _ in range(2))]

    @assemble(family, locals(), globals())
    class PE(Peak):
        def __init__(self):
            
            self.alu: ALU = ALU()

        @name_outputs(PE_res=Out_Data)
        def __call__(self, inst: Inst, inputs : DataInputList, ) -> (Out_Data):
            
            alu_res, alu_res_p, Z, N, C, V = self.alu(inst.alu, inst.signed, inputs[0], inputs[1])
            
            return alu_res
               
    return PE
 
