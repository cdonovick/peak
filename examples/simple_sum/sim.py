from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def simple_sum_fc(family):
    Data = family.BitVector[16]
    class SimpleSum(Peak):
        @name_outputs(out=Data)
        def __call__(self,instr : Instr, a : Data, b : Data):
            subtype, instr = instr.match()
            if subtype is Add:
                res = a + b
            elif subtype is Sub:
                res = a - b
            elif subtype is Add1:
                res = a + Data(1)
            else:
                raise PeakNotImplementedError(op)
            return res

    return SimpleSum
