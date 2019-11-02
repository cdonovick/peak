from .peak import Peak
from hwtypes import BitVector, Bit
import functools

#@functools.lru_cache(maxsize=None)
def gen_register(T,  init : "T"):
    class Register(Peak):
        def __init__(self):
            self.value: T = T(init)

        def __call__(self, value: T, en: Bit) -> T:
            retvalue = self.value
            if en:
                self.value = value
            else:
                # Bug in magma sequential syntax without default values, we
                # explicitly set it for now
                self.value = self.value
            return retvalue

        @classmethod
        def uniquify(cls):
            return f"{T},{init}"
    return Register
