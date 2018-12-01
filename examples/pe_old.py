from bit_vector import BitVector, UIntVector, SIntVector
from .config import config

__all__ = ['PE']

DATAWIDTH = 16

CONST = 0
VALID = 1
BYPASS = 2
DELAY = 3

BITZERO = BitVector(0, num_bits=1)
ZERO = BitVector(0, num_bits=DATAWIDTH)


def msb(value):
    return value[-1]


def signed(value):
    return SIntVector(value._value, value.num_bits)


class Register:

    def __init__(self, mode, init, width):
        self.mode = mode
        self.value = BitVector(init, num_bits=width)
        self.width = width
        self.last_clk = 0  # TODO: clk initialized to 0, should it be?

    @property
    def const(self):
        return self.mode == CONST

    def __call__(self, value, clk, clk_en):
        if not isinstance(value, BitVector):
            value = BitVector(value, self.width)

        if self.mode in [DELAY, VALID]:
            retvalue = self.value
            # TODO: Assumes posedge
            if not self.last_clk and clk:
                if self.mode == DELAY or clk_en:
                    self.value = value
                    retvalue = value
            self.last_clk = clk
            return retvalue
        elif self.mode == CONST:
            return self.value
        elif self.mode == BYPASS:
            return value
        else:
            raise NotImplementedError()


class ALU:

    def __init__(self, op, opcode, width, signed=False, double=False):
        self.op = op
        self.signed = signed
        self.double = double
        self.opcode = opcode
        self.width = width
        self._carry = False

    def __call__(self, op_a=0, op_b=0, c=0, op_d_p=0):
        bv = UIntVector if not self.signed else  SIntVector
        a = bv(op_a, num_bits=self.width)
        b = bv(op_b, num_bits=self.width)
        c = bv(c, num_bits=self.width)
        d = bv(op_d_p, num_bits=self.width)
        res = self.op(a, b, c, d)
        if self._carry:
            res_p = BitVector(a._value + b._value >= (2 ** self.width), 1)
            return res, res_p
        return res


    def carry(self):
        self._carry = True


class COND:

    def __init__(self, cond, signed=False):
        self.cond = cond
        self.signed = signed

    def __call__(self, a, b, res):
        return_vals = self.compare(a, b, res)
        return self.cond(*return_vals)

    def compare(self, a, b, res):
        eq = a == b
        eq = eq.as_int()
        a_msb = msb(a)
        b_msb = msb(b)
        c_msb = msb(res)
        if self.signed:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (~a_msb & b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (a_msb & ~b_msb) | eq) & 1
        else:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (a_msb & ~b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (~a_msb & b_msb) | eq) & 1
        return BitVector(ge, num_bits=1), \
               BitVector(eq, num_bits=1), \
               BitVector(le, num_bits=1), \



class PE:

    def __init__(self, opcode, alu=None, signed=0):
        self.alu(opcode, signed, alu)
        self.cond()
        self.reg()
        self.place()
        self._lut = None
        self.flag_sel = 0x0
        self.irq_en_0 = False
        self.irq_en_1 = False
        self._debug_trig = 0x0
        self._debug_trig_p = 0x0

    def __call__(self, data0=0, data1=0, c=0, bit0=0, bit1=0, bit2=0, clk=0, clk_en=1):

        ra = self.RegA(data0, clk, clk_en)
        rb = self.RegB(data1, clk, clk_en)
        rc = self.RegC(c, clk, clk_en)
        rd = self.RegD(bit0, clk, clk_en)
        re = self.RegE(bit1, clk, clk_en)
        rf = self.RegF(bit2, clk, clk_en)

        res = ZERO
        res_p = BITZERO
        alu_res_p = BITZERO

        if self._add:
            add = self._add(ra, rb, rc, rd)

        if self._alu:
            res = self._alu(ra, rb, rc, rd)
            if isinstance(res, tuple):
                res, alu_res_p = res[0], res[1]

        lut_out = BITZERO
        if self._lut:
            lut_out = self._lut(rd, re, rf)

        res_p = self.get_flag(ra, rb, rc, rd, res, alu_res_p, lut_out)
        if not isinstance(res_p, BitVector):
            assert res_p in {0, 1}, res_p
            res_p = BitVector(res_p, 1)
        # if self._cond:
        #     res_p = self._cond(ra, rb, res)

        # Set internal flags to determine whether debug trigger should be raised
        # for both the result and the predicate.
        self.raise_debug_trig = res != self._debug_trig
        self.raise_debug_trig_p = res_p != self._debug_trig_p

        return res.as_uint(), res_p.as_uint(), self.get_irq_trigger()

    def get_irq_trigger(self):
        return (self.irq_en_0 and self.raise_debug_trig_p) \
            or (self.irq_en_1 and self.raise_debug_trig)

    def irq_en(self, en_0=True, en_1=True):
        self.irq_en_0 = en_0
        self.irq_en_1 = en_1
        return self

    def debug_trig(self, value):
        self._debug_trig = value
        return self

    def debug_trig_p(self, value):
        self._debug_trig_p = value
        return self

    def get_flag(self, ra, rb, rc, rd, alu_res, alu_res_p, lut_out):
        Z = alu_res == 0
        if self._opcode == 0x0: # add
            C = (ra.ext(1) + rb.ext(1) + rd.ext(1))[16]
        elif self._opcode in [0x1, 0x4, 0x5]: # sub
            C = (ra.ext(1) + (~rb).ext(1) + 1)[16]
        elif self._opcode == 0x3: # abs
            C = ((~ra).ext(1) + 1)[16]
        else:
            C = (ra.ext(1) + rb.ext(1))[16]
        N = alu_res[15]
        if self._opcode == 0x0: # add
            V = (ra[15] == rb[15]) and (ra[15] != (ra + rb + rd)[15])
        elif self._opcode == 0x1: # sub
            V = (ra[15] != rb[15]) and (ra[15] != (ra + ~rb + 1)[15])
        elif self._opcode == 0x3: # abs
            V = ra == 0x8000
            # V = alu_res[15]
        elif self._opcode in [0xb, 0xc]: # mul0, mul1
            V = (ra * rb)[15] if (ra[15] == rb[15]) else (ra * rb)[15] == 0 and (ra != 0 or rb != 0)
        elif self._opcode == 0xd:
            V = 0
        elif self._opcode in [0x4, 0x5]:
            V = 0
        else:
            V = (ra[15] == rb[15]) and (ra[15] != (ra + rb)[15])
        if self._opcode in [0x12, 0x13, 0x14,  # and, or, xor clear overflow flag
                                  0xf, 0x11,         # lshl, lshr
                                  0x8]:              # sel
            V = 0
        if self.flag_sel == 0x0:
            return Z
        elif self.flag_sel == 0x1:
            return not Z
        elif self.flag_sel == 0x2:
            return C
        elif self.flag_sel == 0x3:
            return not C
        elif self.flag_sel == 0x4:
            return N
        elif self.flag_sel == 0x5:
            return not N
        elif self.flag_sel == 0x6:
            return V
        elif self.flag_sel == 0x7:
            return not V
        elif self.flag_sel == 0x8:
            return C and not Z
        elif self.flag_sel == 0x9:
            return not C or Z
        elif self.flag_sel == 0xA:
            return N == V
        elif self.flag_sel == 0xB:
            return N != V
        elif self.flag_sel == 0xC:
            return not Z and (N == V)
        elif self.flag_sel == 0xD:
            return Z or (N != V)
        elif self.flag_sel == 0xE:
            return lut_out
        elif self.flag_sel == 0xF:
            return alu_res_p
        raise NotImplementedError(self.flag_sel)

    def alu(self, opcode, signed, _alu):
        self._opcode = opcode
        self._signed = signed
        self._alu = ALU(_alu, opcode, DATAWIDTH, signed=signed)
        return self

    def signed(self, _signed=True):
        self._signed = _signed
        self._alu.signed = _signed
        return self

    def flag(self, flag_sel):
        self.flag_sel = flag_sel
        return self

    def add(self, _add=None):
        self._add = _add
        return self

    def carry(self):
        self._alu.carry()
        return self

    def cond(self, _cond=None):
        self._add = None
        self._cond = None
        if _cond:
            self.add(lambda a, b, c, d: a+b if _cond else None)
            self._cond = COND(_cond, self._signed)
        return self

    def reg(self):
        self.regcode = 0
        self.rega()
        self.regb()
        self.regc()
        self.regd()
        self.rege()
        self.regf()
        return self

    def rega(self, regmode=BYPASS, regvalue=0):
        self.RegA = Register(regmode, regvalue, DATAWIDTH)
        self.raconst = regvalue
        self.regcode &= ~(3 << 0)
        self.regcode |= config('aa', a=regmode)
        return self

    def regb(self, regmode=BYPASS, regvalue=0):
        self.RegB = Register(regmode, regvalue, DATAWIDTH)
        self.rbconst = regvalue
        self.regcode &= ~(3 << 2)
        self.regcode |= config('aa', a=regmode) << 2
        return self

    def regc(self, regmode=BYPASS, regvalue=0):
        self.RegC = Register(regmode, regvalue, DATAWIDTH)
        self.rcconst = regvalue
        return self

    def regd(self, regmode=BYPASS, regvalue=0):
        self.RegD = Register(regmode, regvalue, 1)
        self.rdconst = regvalue
        self.regcode &= ~(3 << 8)
        self.regcode |= config('aa', a=regmode) << 8
        return self

    def rege(self, regmode=BYPASS, regvalue=0):
        self.RegE = Register(regmode, regvalue, 1)
        self.reconst = regvalue
        self.regcode &= ~(3 << 10)
        self.regcode |= config('aa', a=regmode) << 10
        return self

    def regf(self, regmode=BYPASS, regvalue=0):
        self.RegF = Register(regmode, regvalue, 1)
        self.rfconst = regvalue
        self.regcode &= ~(3 << 12)
        self.regcode |= config('aa', a=regmode) << 12
        return self

    @property
    def instruction(self):
        irq_en = self.irq_en_0 | (self.irq_en_1 << 1)
        return config('r' * 14 + 'ffffiia00soooooo',
                      o=self._opcode, s=self._signed, a=0, i=irq_en, f=self.flag_sel, r=self.regcode)


    def lut(self, code=None):
        def _lut(bit0, bit1, bit2):
            idx = (bit2.as_uint() << 2) | (bit1.as_uint() << 1) | bit0.as_uint()
            return (code >> idx) & 1
        self._lut = _lut
        # if self.lut:
        #     self.opcode |= 1 << 9
        # else:
        #     self.opcode &= ~(1 << 9)
        return self

    def dual(self):
        self.opcode |= 1 << 7
        return self

    def place(self, x=None, y=None):
        self.x = x
        self.y = y
        return self
