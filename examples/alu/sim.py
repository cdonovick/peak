from peak import Peak, name_outputs, PeakNotImplementedError
import typing as  tp
from .isa import *
from hwtypes import TypeFamily

def gen_ALU(width=16):
    def family_closure(family):
        Data = family.BitVector[width]
        def alu(op : ALUOP, a : Data, b : Data):
            if op == ALUOP.Neg:
                a = Data(0)
            elif op == ALUOP.Not:
                a = Data(-1)

            if op == ALUOP.Add:
                res = a + b
            elif (op == ALUOP.Sub) | (op == ALUOP.Neg):
                res = a-b
            elif op == ALUOP.And:
                res = a & b
            elif op == ALUOP.Or:
                res = a | b
            elif (op == ALUOP.XOr) | (op == ALUOP.Not):
                res = a ^ b
            else:
                raise PeakNotImplementedError(op)
            return res

        class ALU(Peak):

            @name_outputs(alu_res=Data)
            def __call__(self,inst : Inst, a : Data, b : Data):
                return alu(inst.alu_op,a,b)
        return ALU
    return family_closure