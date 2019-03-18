from .peak import Peak
from hwtypes import BitVector
import magma as m


def gen_register(T, init=0):
    family = T.get_family()

    class Register(Peak):
        def __init__(self):
            self.value: T = T(init)

        def __call__(self, value: T=None, en: family.Bit=1) -> T:
            retvalue = self.value
            if value is not None and en:
                assert value is not None
                self.value = value
            return retvalue

    if family.Bit is m.Bit:
        Register = m.circuit.sequential(Register)
    return Register
