from .peak import Peak
from hwtypes import BitVector
import magma as m


def gen_register(T, mode="sim"):
    if mode == "sim":
        family = BitVector.get_family()
    elif mode == "rtl":
        family = m.get_family()
    else:
        raise NotImplementedError(mode)

    class Register(Peak):
        def __init__(self, init):
            self.value: T = T(init)

        def __call__(self, value: T=None, en: family.Bit=1) -> T:
            retvalue = self.value
            if value is not None and en:
                assert value is not None
                self.value = value
            return retvalue

    if mode == "sim":
        return Register
    elif mode == "rtl":
        return m.circuit.sequential(Register)
