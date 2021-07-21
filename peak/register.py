import warnings

from .peak import Peak
from .family import AbstractFamily, MagmaFamily
from .features import family_closure, name_outputs
from hwtypes import BitVector
import magma as m
from hwtypes.adt_util import rebind_type

def gen_register(T, init=0):
    warnings.warn("gen_register is deprecated, use family.gen_register",
                   DeprecationWarning)
    @family_closure
    def Register_fc(family: AbstractFamily):
        T_f = rebind_type(T, family)
        return family.gen_register(T_f, init)

    return Register_fc


#Old inteface to gen_register
def gen_register2(family, T, init=0):
    Bit = family.Bit
    class Register(Peak):
        def __init__(self):
            self.value: T = init

        def __call__(self, value : T, en : Bit) -> T:
            assert value is not None
            retvalue = self.value
            if en:
                self.value = value
            else:
                self.value = self.value
            return retvalue

    if family.Bit is m.Bit:
        Register = m.circuit.sequential(Register)
    return Register

def gen_Register3(width, init=None):

    if init is None:
        init = 0

    @family_closure
    def Register3_fc(family):
        T = family.BitVector[width]

        class Register3(Peak):
            def __init__(self):
                self.value: T = T(init)
                self.next_value: T = None

            #equivelent to evaluating 'posedge clk'
            def update_state(self) -> None:
                self.value = self.next_value
                self.next_value = None

            def __call__(self, i: T) -> T:
                self.next_value = i
                return self.value

            def get(self) -> T:
                return self.value

            def set(self, v: T) -> None:
                self.value = v
        return Register3
    return Register3_fc
