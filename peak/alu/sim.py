from .. import Peak, name_outputs
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def gen_alu(family : TypeFamily):
    Bit = family.Bit
    Data = family.BitVector[Datawidth]
    
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
