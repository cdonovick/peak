from .isa import *
from .. import Peak
from bit_vector import BitVector

class Register(Peak):
    def __init__(self, type, init = 0):
        self.type = type
        self.init = init
        self.reset()

    def reset(self):
        self.value = self.init

    def __call__(self, value, clk_en:Bit) -> Data:
        retvalue = self.value
        if clk_en:
            self.value = type(value)
        return retvalue

class RegisterMode(Peak):
    def __init__(self, init = 0):
        self.register = Register(init)

    def reset(self):
        self.register.reset()

    def __call__(self, mode:Mode, const, value, clk_en:Bit):
        if   mode == Mode.CONST:
            return const
        elif mode == Mode.BYPASS:
            return value
        elif mode == Mode.DELAY:
            return self.register(value, mode == Mode.DELAY)
        elif mode == Mode.VALID:
            return self.register(value, clk_en)
        else:
            raise NotImplementedError()

def alu(alu:ALU_Op, signed:Signed, a:Data, b:Data, d:Bit):

    def zext(x,n):
        return BitVector(x.bits()+n*[0])
    def adc(a:Data,b:Data,c:Bit):
        a = zext(a,1)
        b = zext(b,1)
        c = zext(c,16)
        res = a + b + c
        return res[0:-1], Bit(res[-1])
    def mul(a, b, c, d):
        a, b = a.ext(16), b.ext(16)
        return a*b
    def mult0(a, b, c, d):
        return mul(a, b, c, d)[:16], 0
    def mult1(a, b, c, d):
        return mul(a, b, c, d)[8:24], 0
    def mult2(a, b, c, d):
        return mul(a, b, c, d)[16:32], 0

    if signed:
        a = SInt(a)
        b = SInt(b)
        c = SInt(c)

    if   alu == ALU_Op.Add:
        res, res_p = adc(a, b, Bit(0))
    elif alu == ALU_Op.Sub:
        res, res_p = adc(a, ~b, Bit(1))
    elif alu == ALU_Op.Mult0:
        res, res_p = mul0(a, b, c, d)
    elif alu == ALU_Op.Mult1:
        res, res_p = mul1(a, b, c, d)
    elif alu == ALU_Op.Mult2:
        res, res_p = mul1(a, b, c, d)
    elif alu == ALU_Op.GTE_Max:
        res, res_p = a if a >= b else b, a >= b
    elif alu == ALU_Op.LTE_Min:
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
    else:
        raise NotImplementedError(alu)

    Z = res == 0
    N = Bit(res[-1])
    C = res_p
    msba = Bit(a[-1])
    msbb = Bit(b[-1])
    V = (msba & msbb & ~N) or (~msba & ~msbb & N)

    return res, res_p, Z, N, C, V

def lut( lut:LUT_Op, bit0:Bit, bit1:Bit, bit2:Bit) -> Bit:
    i = (int(bit2)<<2) | (int(bit1)<<1) | int(bit0)
    return Bit(lut & (1 << i))
    
def cond(code:Cond_Op, alu:Bit, lut:Bit, Z:Bit, N:Bit, C:Bit, V:Bit) -> Bit:
    if   code == Cond_Op.Z:
        return Z
    elif code == Cond_Op.Z_n:
        return not Z
    elif code == Cond_Op.C or code == Cond_Op.UGE:
        return C
    elif code == Cond_Op.C_n or code == Cond_Op.ULT:
        return not C
    elif code == Cond_Op.N:
        return N
    elif code == Cond_Op.N_n:
        return not N
    elif code == Cond_Op.V:
        return V
    elif code == Cond_Op.V_n:
        return not V
    elif code == Cond_Op.UGT:
        return C and not Z
    elif code == Cond_Op.ULE:
        return not C or Z
    elif code == Cond_Op.SGE:
        return N == V
    elif code == Cond_Op.SLT:
        return N != V
    elif code == Cond_Op.SGT:
        return not Z and (N == V)
    elif code == Cond_Op.SLE:
        return Z or (N != V)
    elif code == Cond_Op.Never:
        return Bit(0)
    elif code == Cond_Op.Always:
        return Bit(1)
    raise NotImplementedError(op)


class PE(Peak):

    def __init__(self):
        self.rega = RegisterMode(Data)
        self.regb = RegisterMode(Data)
        self.regc = RegisterMode(Data)
        self.regd = RegisterMode(Bit)
        self.rege = RegisterMode(Bit)
        self.regf = RegisterMode(Bit) 

    def __call__(self, inst: Inst, \
        data0: Data, data1: Data, data2: Data = Data(0), \
        bit0: Bit = Bit(0), bit1: Bit = Bit(0), bit2: Bit = Bit(0), \
        clk_en: Bit = Bit(1)):

        ra = self.rega(inst.rega, inst.data0, data0, clk_en)
        rb = self.regb(inst.regb, inst.data1, data1, clk_en)
        rc = self.regc(inst.regc, inst.data2, data2, clk_en)
        rd = self.regd(inst.regc, inst.bit0, bit0, clk_en)
        re = self.rege(inst.regd, inst.bit1, bit1, clk_en)
        rf = self.regf(inst.regf, inst.bit2, bit2, clk_en)

        alu_res, alu_res_p, Z, N, C, V= alu(inst.alu, inst.signed, ra, rb, rd)
        lut_res = lut(inst.lut, rd, re, rf)
        res_p = cond(inst.cond, alu_res, lut_res, Z, N, C, V)
        irq = Bit(0)

        return alu_res, res_p, irq


