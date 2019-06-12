from .peak import Peak
from hwtypes import BitVector
import magma as m


def gen_register(family, T, init=0):
    class Register(Peak):
        def __init__(self):
            self.value: T = init

        def __call__(self, value: T, en: family.Bit) -> T:
            assert value is not None
            retvalue = self.value
            if en:
                self.value = value
            else:
                # Bug in magma sequential syntax without default values, we
                # explicitly set it for now
                self.value = self.value
            return retvalue

    if family.Bit is m.Bit:
        Register = m.circuit.sequential(Register)
    return Register
