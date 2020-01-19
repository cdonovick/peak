from .peak import Peak, family_closure, name_outputs, update_peak
from hwtypes import BitVector
import magma as m
from hwtypes.adt_util import rebind_type

def gen_register(T, init=0):
    @family_closure
    def Register_fc(family):
        T_f = rebind_type(T, family)
        init_f = T_f(init)

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
        if family.Bit is m.Bit:
            Register = m.circuit.sequential(Register)
        return update_peak(Register, family)
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
