from peak import Peak, name_outputs, PeakNotImplementedError, gen_register
import typing as  tp
from .isa import *
from hwtypes import BitVector

def gen_seq(width=16):
    Data = BitVector[width]
    Reg = gen_register(Data, 0)
    class ALU(Peak):
        def __init__(self):
            self.reg: Data = Reg()

        @name_outputs(alu_res=Data)
        def __call__(self, inst : Inst, a : Data, b : Data):
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
            self.reg(self.reg+res)
            return res
    return ALU
