from .peak import Peak
from hwtypes import BitVector, Bit

_cache_ = {}
def gen_register(T):
    if T in _cache_:
        return _cache_[T]
    class Register(Peak):
        def __init__(self, init : T):
            self.value: T = init

        def __call__(self, value: T, en: Bit) -> T:
            retvalue = self.value
            if en:
                self.value = value
            else:
                # Bug in magma sequential syntax without default values, we
                # explicitly set it for now
                self.value = self.value
            return retvalue
    _cache_[T] = Register
    return Register
