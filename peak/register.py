from .peak import Peak
from .family import AbstractFamily
from .features import family_closure, name_outputs
from hwtypes import BitVector
import magma as m
from hwtypes.adt_util import rebind_type

def gen_register(T, init=0):
    @family_closure
    def Register_fc(family: AbstractFamily):
        T_f = rebind_type(T, family)
        init_f = T_f(init)

        @family.assemble(locals(), globals())
        class Register(Peak):
            def __init__(self):
                self.value: T_f = init_f

            def __call__(self, value: T_f, en: family.Bit) -> T_f:
                assert value is not None
                retvalue = self.value
                if en:
                    self.value = value
                else:
                    self.value = self.value
                return retvalue

            def read(self) -> T_f:
                return self.value

            def write(self, val : T_f):
                self.value = val
        return Register

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
