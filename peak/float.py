from functools import lru_cache
from types import SimpleNamespace
from . import Peak, family_closure
from hwtypes import BitVector
from hwtypes import TypeFamily
from .family import BlackBox

@lru_cache(None)
def Float(frac, exp):
    width = frac + exp + 1
    Data = BitVector[width]

    @family_closure
    def add_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class add(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return add

    @family_closure
    def mul_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class mul(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return mul

    @family_closure
    def sqrt_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class sqrt(Peak, BlackBox):
            def __call__(self, in_1: Data) -> Data:
                ...
        return sqrt


    return SimpleNamespace(**locals())
