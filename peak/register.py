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


# its really hard (impossible?) to support both call
# and update_state paradigms
def gen_update_register(T, init=0):
    @family_closure
    def gen_register_fc(family):
        T_f = rebind_type(T, family)
        if isinstance(family, MagmaFamily):
            return family.gen_register(T_f, init)
        else:
            @family.assemble(locals(), globals())
            class Register(Peak, gen_ports=True):
                def __init__(self):
                    self._value: T_f = T_f(init)
                    self._next_value: T_f = T_f(init)

                @name_outputs(out=T)
                def __call__(self, value: T, en: family.Bit) -> T:
                    if en:
                        self._next_value = value

                    return self._value

                def prev(self) -> T:
                    return self._value

                def _update_state_(self):
                    self._value = self._next_value

            return Register
    return gen_register_fc
