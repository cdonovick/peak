from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import BitVector

def gen_ALU(width=16):
    Data = BitVector[width]
    class ALU(Peak):
        def __init__(self):
            self.bit1 = gen_register()

        @name_outputs(alu_res=Data)
        def __call__(self,inst : Inst, a : Data, b : Data):
            op = inst.alu_op
            if op == ALUOP.Add:
                res = a + b
            elif (op == ALUOP.Sub):
                res = a-b
            elif op == ALUOP.And:
                res = a & b
            elif op == ALUOP.Or:
                res = a | b
            elif (op == ALUOP.XOr):
                res = a ^ b
            else:
                raise PeakNotImplementedError(op)
            return res
    return ALU
