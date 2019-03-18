from .. import Peak, name_outputs
import typing as  tp
from .isa import *
from hwtypes import TypeFamily, BitVector

Data = BitVector[16]

class ALU(Peak):
    def __init__(self, family : TypeFamily, width=16):
        super().__init__(family,width)
    
    def alu(self,op : ALUOP, a : Data, b : Data):
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
    
    @name_outputs(alu_res=Data)
    def __call__(self,inst : Inst, a : Data, b : Data):
        return self.alu(inst.alu_op,a,b)
