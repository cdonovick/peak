from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def gen_simple_sum(width=16):
    Data = BitVector[width]
    Instr = gen_isa(width)
    Op = Instr.op
    Add = Op.field_dict["Add"]
    Sub = Op.field_dict["Sub"]
    Add1 = Op.field_dict["Add1"]
    class SimpleSum(Peak):
        @name_outputs(out=Data)
        def __call__(self,instr : Instr, a : Data, b : Data):
            op = instr.op
            which_inputs = instr.which_inputs
            if op.match(Add):
                op = op[Add]
                if which_inputs is type(which_inputs).Sim:
                    res = a + b
                else :
                    res = op.in0 + op.in1
            elif op.match(Sub):
                op = op[Sub]
                if which_inputs is type(which_inputs).Sim:
                    res = a - b
                else :
                    res = op.in0 - op.in1
            elif op.match(Add1):
                op = op[Add1]
                if which_inputs is type(which_inputs).Sim:
                    res = a + Data(1)
                else :
                    res = op.in0 + Data(1)
            else:
                raise PeakNotImplementedError(op,subtype)
            return res

    return SimpleSum
