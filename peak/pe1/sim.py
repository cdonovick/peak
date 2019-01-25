from bit_vector import BitVector, SIntVector, UIntVector, overflow
from .. import Peak
from .mode import Mode, RegisterMode
from .lut import LUT, lut, Bit
from .cond import Cond, cond
from .isa import *


def gen_alu(BV_t=BitVector, Sign_t=SIntVector, Unsigned_t=UIntVector):
    def Bit(n):
        return BV_t(n, 1)

    def alu(alu:ALU, signed:Signed, a:BV_t, b:BV_t, d:Bit):

        def mul(a, b):
            a, b = a.ext(16), b.ext(16)
            return a*b
        def mult0(a, b):
            res = mul(a, b)
            return res[:16], 0, 0 # wrong C, V
        def mult1(a, b, d):
            res = mul(a, b)
            return res[8:24], 0, 0 # wrong C, V
        def mult2(a, b, c, d):
            res = mul(a, b)
            return res[16:32], 0, 0 # wrong C, V

        if signed:
            a = Sign_t(a)
            b = Sign_t(b)

        C = 0
        V = 0
        if   alu == ALU.Add:
            res, C = a.adc(b, Bit(0))
            #V = overflow(a, b, res)
            res_p = C
        elif alu == ALU.Sub:
            b_not = ~b
            res, C = a.adc(b_not, Bit(1))
            #V = overflow(a, b_not, res)
            res_p = C
        elif alu == ALU.Mult0:
            res, C, V = mult0(a, b)
            res_p = C
        elif alu == ALU.Mult1:
            res, C, V = mult0(a, b)
            res_p = C
        elif alu == ALU.Mult2:
            res, C, V = mult0(a, b)
            res_p = C
        elif alu == ALU.GTE_Max:
            # C, V = a-b?
            res, res_p = a if a >= b else b, a >= b
        elif alu == ALU.LTE_Min:
            # C, V = a-b?
            res, res_p = a if a <= b else b, a <= b
        elif alu == ALU.Abs:
            res, res_p = a if a >= 0 else -a, Bit(a[-1])
        elif alu == ALU.Sel:
            res, res_p = a if d else b, 0
        elif alu == ALU.And:
            res, res_p = a & b, 0
        elif alu == ALU.Or:
            res, res_p = a | b, 0
        elif alu == ALU.XOr:
            res, res_p = a ^ b, 0
        elif alu == ALU.SHR:
            res, res_p = a >> b, 0
        elif alu == ALU.SHL:
            res, res_p = a << b, 0
        elif alu == ALU.Neg:
            if signed:
                res, res_p = ~a+Bit(1), 0
            else:
                res, res_p = ~a, 0
        else:
            raise NotImplementedError(alu)

        Z = res == 0
        N = Bit(res[-1])

        return res, res_p, Z, N, C, V

    return alu

class PE(Peak):

    def __init__(self):
        # Data registers
        self.rega = RegisterMode(Data)
        self.regb = RegisterMode(Data)

        # Bit Registers
        self.regd = RegisterMode(Bit)
        self.rege = RegisterMode(Bit)
        self.regf = RegisterMode(Bit)

    def __call__(self, inst: Inst, \
        data0: Data, data1: Data = Data(0), \
        bit0: Bit = Bit(0), bit1: Bit = Bit(0), bit2: Bit = Bit(0), \
        clk_en: Bit = Bit(1)):

        ra = self.rega(inst.rega, inst.data0, data0, clk_en)
        rb = self.regb(inst.regb, inst.data1, data1, clk_en)

        rd = self.regd(inst.regd, inst.bit0, bit0, clk_en)
        re = self.rege(inst.rege, inst.bit1, bit1, clk_en)
        rf = self.regf(inst.regf, inst.bit2, bit2, clk_en)

        alu = gen_alu()

        alu_res, alu_res_p, Z, N, C, V = alu(inst.alu, inst.signed, ra, rb, rd)
        lut_res = lut(inst.lut, rd, re, rf)
        res_p = cond(inst.cond, alu_res, lut_res, Z, N, C, V)
        irq = Bit(0)

        return alu_res, res_p, irq


