from .isa import *
from .. import Peak

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

class ALU(Peak):
    def __call__(self, alu:ALU_Op, signed:Signed, a:Data, b:Data, d:Bit):

        if signed:
            a = SInt(a)
            b = SInt(b)
            c = SInt(c)

        if alu == ALU_Op.Add:
            res = a + b
            res_p = 0
        elif alu == ALU_Op.Sub:
            res = a - b
            res_p = 0
        elif alu == ALU_Op.And:
            res = a & b
            res_p = 0
        elif alu == ALU_Op.Or:
            res = a | b
            res_p = 0
        elif alu == ALU_Op.XOr:
            res = a ^ b
            res_p = 0
        else:
            raise NotImplementedError(alu)

        Z = res == 0
        N = res[-1]
        C = res_p
        V = (a[-1] & b[-1] & ~N) or (~a[-1] & ~b[-1] & N)

        return res, res_p, Z, N, C, V

class LUT(Peak):
    def __call__(self, lut:LUT_Op, bit0:Bit, bit1:Bit, bit2:Bit) -> Bit:
        i = (int(bit2)<<2) | (int(bit1)<<1) | int(bit0)
        return lut & (1 << i)
    
class Cond(Peak):
    def __call__(self, op:Cond_Op, 
         alu:Bit, lut:Bit, Z:Bit, N:Bit, C:Bit, V:Bit) -> Bit:

        if op == 0x0:
            return Z
        elif op == 0x1:
            return not Z
        elif op == 0x2:
            return C
        elif op == 0x3:
            return not C
        elif op == 0x4:
            return N
        elif op == 0x5:
            return not N
        elif op == 0x6:
            return V
        elif op == 0x7:
            return not V
        elif op == 0x8:
            return C and not Z
        elif op == 0x9:
            return not C or Z
        elif op == 0xA:
            return N == V
        elif op == 0xB:
            return N != V
        elif op == 0xC:
            return not Z and (N == V)
        elif op == 0xD:
            return Z or (N != V)
        elif op == 0xE:
            return lut
        elif op == 0xF:
            return alu

        raise NotImplementedError(op)


class PE(Peak):

    def __init__(self):
        self.rega = RegisterMode(Data)
        self.regb = RegisterMode(Data)
        self.regc = RegisterMode(Data)
        self.regd = RegisterMode(Bit)
        self.rege = RegisterMode(Bit)
        self.regf = RegisterMode(Bit) 

        self.lut = LUT()
        self.alu = ALU()
        self.cond = Cond()

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

        res, res_p, Z, N, C, V= self.alu(inst.alu, inst.signed, ra, rb, rd)
        #lut = self.lut(inst.lut, rd, re, rf)
        #res_p = self.cond(inst.cond, res, lut, Z, N, C, V)
        irq = Bit(0)

        return res, res_p, irq


