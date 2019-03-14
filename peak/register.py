from .peak import Peak
from hwtypes import TypeFamily


def gen_register(family: TypeFamily, datawidth=None):
    T = family
    if datawidth is not None:
        T = T[datawidth]

    class Register(Peak):
        def __init__(self, init):
            self.init: T = init
            self.reset()

        def reset(self):
            self.value = self.init

        def __call__(self, value=None, en=1):
            retvalue = self.value
            if value is not None and en:
                assert value is not None
                self.value = value
            return retvalue

    return Register
