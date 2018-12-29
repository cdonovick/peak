from bit_vector import BitVector, SIntVector
from .. import Peak
from .mode import Mode, RegisterMode
from .lut import Bit, LUT, lut
from .cond import Cond, cond
from .isa1 import *

def alu(alu:ALU_Op, signed:Signed, a:Data, b:Data, d:Bit):

    def zext(x,n):
        return BitVector(x.bits()+n*[0])
    def adc(a:Data,b:Data,c:Bit):
        msba = Bit(a[-1])
        msbb = Bit(b[-1])
        a = zext(a,1)
        b = zext(b,1)
        c = zext(c,16)
        res = a + b + c
        C = Bit(res[-1])
        res = res[0:-1]
        N = Bit(res[-1])
        V = (msba & msbb & ~N) or (~msba & ~msbb & N)
        return res, C, V
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
        a = SIntVector(a)
        b = SIntVector(b)

    C = 0
    V = 0
    if   alu == ALU_Op.Add:
        res, C, V = adc(a, b, Bit(0))
        res_p = C
    elif alu == ALU_Op.Sub:
        res, C, V = adc(a, ~b, Bit(1)) 
        res_p = C
    elif alu == ALU_Op.Mult0:
        res, C, V = mul0(a, b)
        res_p = C
    elif alu == ALU_Op.Mult1:
        res, C, V = mul1(a, b)
        res_p = C
    elif alu == ALU_Op.Mult2:
        res, C, V = mul1(a, b) 
        res_p = C
    elif alu == ALU_Op.GTE_Max:
        # C, V = a-b?
        res, res_p = a if a >= b else b, a >= b
    elif alu == ALU_Op.LTE_Min:
        # C, V = a-b?
        res, res_p = a if a <= b else b, a <= b
    elif alu == ALU_Op.Abs:
        res, res_p = a if a >= 0 else -a, Bit(a[-1])
    elif alu == ALU_Op.Sel:
        res, res_p = a if d else b, 0
    elif alu == ALU_Op.And:
        res, res_p = a & b, 0
    elif alu == ALU_Op.Or:
        res, res_p = a | b, 0
    elif alu == ALU_Op.XOr:
        res, res_p = a ^ b, 0
    elif alu == ALU_Op.SHR:
        res, res_p = a >> b[:4], 0
    elif alu == ALU_Op.SHL:
        res, res_p = a << b[:4], 0
    elif alu == ALU_Op.Neg:
        if signed:
            res, res_p = ~a+Bit(1), 0
        else:
            res, res_p = ~a, 0
    else:
        raise NotImplementedError(alu)

    Z = res == 0
    N = Bit(res[-1])

    return res, res_p, Z, N, C, V

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

        alu_res, alu_res_p, Z, N, C, V= alu(inst.alu, inst.signed, ra, rb, rd)
        lut_res = lut(inst.lut, rd, re, rf)
        res_p = cond(inst.cond, alu_res, lut_res, Z, N, C, V)
        irq = Bit(0)

        return alu_res, res_p, irq


