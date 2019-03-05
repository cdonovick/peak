from .. import Peak, name_outputs
import typing as  tp
from .isa import *
from hwtypes import AbstractBitVector

def gen_alu(BV_t : tp.Type['AbstractBitVector']):
    Bit = BV_t[1]
    Data = BV_t[Datawidth]
    
    @name_outputs(alu_res=Data)
    def PE(inst : Inst, a : Data, b : Data):
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
                raise NotImplementedError(op)
            return res
        return alu(inst.alu_op,a,b)
    return PE
