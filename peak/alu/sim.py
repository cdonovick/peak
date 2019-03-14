from .. import Peak, name_outputs
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

class ALU(Peak):
    def __init__(self,family : TypeFamily):
        self.Bit = family.Bit
        self.Data = family.BitVector[Datawidth]

    @name_outputs(alu_res=Data)
    def __call__(self, inst : Inst, a : Data, b : Data):
        op = inst.alu_op
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
            raise NotImplementedError(op)
        return res
