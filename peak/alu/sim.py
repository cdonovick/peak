from bit_vector import BitVector, SIntVector, UIntVector, overflow
from .. import Peak, name_outputs
from .isa import *

def gen_alu(BV_t=BitVector):
    
    def alu(alu:ALU, a:BV_t, b:BV_t):

        if alu == ALUOP.Add:
            res = a + b
        elif alu == ALUOP.Sub:
            res = a-b
        elif alu == ALUOP.And:
            res = a & b
        elif alu == ALUOP.Or:
            res = a | b
        elif alu == ALUOP.XOr:
            res = a ^ b
        else:
            raise NotImplementedError(alu)
        return res

    return alu

class ALU(Peak):
    def __init__(self):
        pass

    @name_outputs(alu_res=Data)
    def __call__(self, inst:Inst, data0: Data, data1: Data):
        alu = gen_alu()
        alu_res = alu(inst.alu, data0, data1)
        return alu_res
