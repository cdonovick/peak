from peak.assembler import Assembler
from peak import Peak, family_closure
from peak import family
from peak.family import AbstractFamily

from hwtypes import Bit, BitVector, Tuple

from examples.demo_pes.pe6.sim import PE_fc, Inst

@family_closure
def PE_wrapped_fc(family: AbstractFamily):
    Data = family.BitVector[16]
    Bit = family.Bit

    @family.assemble(locals(), globals())
    class PE_wrapped(Peak):
        def __init__(self):
            self.PE : PE_fc(family) = PE_fc(family)()

        def __call__(self, inst : Inst, data0 : Data, data1 : Data) -> (Data, Data, Bit):
            out_tuple, bit = self.PE(inst, data0, data1)
            return out_tuple[0], out_tuple[1], bit
    
    return PE_wrapped

def test_wrapper():

    PE_py = PE_fc.Py
    PE_smt = PE_fc.SMT
    PE_magma = PE_fc.Magma

    PE_py = PE_wrapped_fc.Py
    PE_smt = PE_wrapped_fc.SMT
    PE_magma = PE_wrapped_fc.Magma

