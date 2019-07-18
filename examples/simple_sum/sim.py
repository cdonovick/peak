from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def simple_sum_fc(family):
    Data = family.BitVector[16]
    Instr = gen_isa(family)
    Op = Instr.op
    class SimpleSum(Peak):
        @name_outputs(out=Data)
        def __call__(self,instr : Instr, a : Data, b : Data):
            op = instr.op
            which_inputs = instr.which_inputs
            subtype, op = op.match()
            if subtype is Op.Add:
                if which_inputs is type(which_inputs).Sim:
                    res = a + b
                else :
                    res = op.in0 + op.in1
            elif subtype is Op.Sub:
                if which_inputs is type(which_inputs).Sim:
                    res = a - b
                else :
                    res = op.in0 - op.in1
            elif subtype is Op.Add1:
                if which_inputs is type(which_inputs).Sim:
                    res = a + Data(1)
                else :
                    res = op.in0 + Data(1)
            else:
                raise PeakNotImplementedError(op)
            return res

    return SimpleSum
