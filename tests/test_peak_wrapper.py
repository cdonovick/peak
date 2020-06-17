from peak.assembler import Assembler
from peak import Peak, family_closure
from peak import family
from peak.family import AbstractFamily
from peak import peak_wrapper

from hwtypes import Bit, BitVector, Tuple

import fault
import magma
import itertools

from examples.demo_pes.pe7.sim import PE_fc, Inst

# @family_closure
# def PE_wrapped_fc(family: AbstractFamily):
#     Data = family.BitVector[16]
#     Bit = family.Bit
#     inputs_tuple_t = Tuple[Data, Data]
#     inputs_constructor = family.get_constructor(inputs_tuple_t)
#     bit_inputs_tuple_t = Tuple[Bit, Bit]
#     bit_inputs_constructor = family.get_constructor(bit_inputs_tuple_t)

#     @family.assemble(locals(), globals())
#     class PE_wrapped(Peak):
#         def __init__(self):
#             self.PE : PE_fc(family) = PE_fc(family)()

#         def __call__(self, inst : Inst, inputs0 : Data, inputs1 : Data, data : Data, bit_inputs0 : Bit, bit_inputs1 : Bit) -> (Data, Data, Bit):
#             inputs_constructed = inputs_constructor(*[inputs0, inputs1])
#             bit_inputs_constructed = bit_inputs_constructor(*[bit_inputs0, bit_inputs1])
            
#             out_tuple, out1 = self.PE(inst, inputs_constructed, data, bit_inputs_constructed)
#             return out_tuple[0], out_tuple[1], out1
    
#     return PE_wrapped

def test_wrapper():

    PE_wrapped_fc = peak_wrapper.wrap_peak_class(PE_fc, Inst)

    PE_py = PE_fc.Py
    PE_smt = PE_fc.SMT
    PE_magma = PE_fc.Magma

    PE_py = PE_wrapped_fc.Py
    PE_smt = PE_wrapped_fc.SMT
    PE_magma = PE_wrapped_fc.Magma

