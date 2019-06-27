import typing as  tp
import operator
from .isa import *
import functools as ft
from peak import name_outputs, Peak

from hwtypes import TypeFamily

def gen_alu(family : TypeFamily):
    Bit = family.Bit
    Data = family.BitVector[DATAWIDTH]

    class Alu(Peak):
        @name_outputs(res=Data,flag_out=Bit)
        def __call__(self, inst : INST, data0 : Data, data1 : Data):
            def alu(inst : ALU_INST, data0 : Data, data1 : Data, bit0 : Bit):
                if inst == ALU_INST.Add:
                    res, carry = data0.adc(data1, bit0)
                elif inst == ALU_INST.And:
                    res = data0 & data1
                    carry = Bit(0)
                elif inst == ALU_INST.Xor:
                    res = data0 ^ data1
                    carry = Bit(0)
                elif inst == ALU_INST.Shft:
                    res = data0.bvshl(data1)
                    carry = Bit(0)
                else:
                    raise TypeError()

                zero = ~ft.reduce(operator.or_, res, Bit(0))
                return res, carry, zero

            bit0 = Bit(0)
            res, _, _ = alu(inst.ALU, data0, data1, bit0)
            flag_out = Bit(0)
            assert isinstance(flag_out, Bit)
            assert isinstance(res, Data)
            return res, flag_out

    return Alu
