from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def gen_alu(family : TypeFamily, width=16):
    Data = family.BitVector[16]
    def alu(op : ALUOP, a : Data, b : Data):
        if op == ALUOP.Add:
            res = a + b
        elif op == ALUOP.Sub:
            res = a-b
        elif op == ALUOP.And:
            res = a & b
        elif op == ALUOP.Or:
            res = a | b
        elif op == ALUOP.XOr:
            res = a ^ b
        else:
            raise PeakNotImplementedError(op)
        return res

    class ALU(Peak):

        @name_outputs(alu_res=Data)
        def __call__(self,inst : Inst, a : Data, b : Data):
            return alu(inst.alu_op,a,b)
    return ALU
