import typing as  tp
import operator
from .isa import *
import functools as ft

from bit_vector import AbstractBitVector


def gen_alu(BV_t : tp.Type['AbstractBitVector']):
    def Bit(value):
        return BV_t(value, 1)

    def Data(value):
        return BV_t(value, DATAWIDTH)


    def alu(inst : INST, data0 : Data, data1 : Data, bit0 : Bit):
        def _flag_mux(inst : FLAG_INST, carry, zero):
            if inst == FLAG_INST.C:
                return carry
            elif inst ==  FLAG_INST.Z:
                return zero
            else:
                raise TypeError()

        def _alu(inst : ALU_INST, data0 : Data, data1 : Data, bit0 : Bit):
            if inst == ALU_INST.Add:
                res, carry = data0.adc(data1, bit0)
            elif inst == ALU_INST.Neg:
                res = -data0
                carry = Bit(0)
            elif inst == ALU_INST.And:
                res = data0 & data1
                carry = Bit(0)
            elif inst == ALU_INST.Or:
                res = data0 | data1
                carry = Bit(0)
            elif inst == ALU_INST.Not:
                res = ~data0
                carry = Bit(0)
            else:
                raise TypeError()

            zero = ~ft.reduce(operator.or_, res, Bit(0))
            return res, carry, zero

        res, carry, zero = _alu(inst.ALU, data0, data1, bit0)
        flag = _flag_mux(inst.FLAG, carry, zero)
        return res, flag

    in_width_map = {
            'data0' : DATAWIDTH,
            'data1' : DATAWIDTH,
            'bit0'  : 1,
    }
    out_width_map = {
            0 : DATAWIDTH,
            1 : 1,
    }
    return alu, in_width_map, out_width_map
