from dataclasses import dataclass
from peak import Bits, Enum, Product

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

Bit = Bits(1)

DATAWIDTH = 16
Data = Bits(DATAWIDTH)
Data0 = Bits(DATAWIDTH)
Data1 = Bits(DATAWIDTH)
Bit0 = Bits(1)
Bit1 = Bits(1)
Bit2 = Bits(1)

class Mode:
    CONST = 0
    VALID = 1
    BYPASS = 2
    DELAY = 3

RegA = Bits(2)
RegB = Bits(2)
RegD = Bits(2)
RegE = Bits(2)
RegF = Bits(2)

class ALU_Op(Enum):
    Add = 0
    Sub = 1
    Abs = 3
    GTE_Max = 4
    LTE_Min = 5
    Sel = 8
    Mult0 = 0xb
    Mult1 = 0xc
    Mult2 = 0xd
    SHR = 0xf
    SHL = 0x11
    Or = 0x12
    And = 0x13
    XOr = 0x14

Signed = Bits(1)

class Cond_Op(Enum):
    Z = 0    # EQ
    Z_n = 1  # NE
    C = 2    # UGE
    C_n = 3  # ULT
    N = 4    # <  0
    N_n = 5  # >= 0
    V = 6    # Overflow
    V_n = 7  # No overflow
    EQ = 0
    NE = 1
    UGE = 2
    ULT = 3
    UGT = 8
    ULE = 9
    SGE = 10
    SLT = 11
    SGT = 12
    SLE = 13
    LUT = 14
    ALU = 15

LUT_Op = Bits(8)

@dataclass
class Inst(Product):
    signed:Signed = Signed(0)
    alu:ALU_Op = ALU_Op.Add
    lut:LUT_Op = LUT_Op(0)
    cond:Cond_Op = Cond_Op.Z
    data0:Data0 = Data0(0)
    data1:Data1 = Data1(0)
    bit0:Bit0 = Bit0(0)
    bit1:Bit1 = Bit1(0)
    bit2:Bit2 = Bit2(0)
    rega:RegA = RegA(Mode.BYPASS)
    regb:RegB = RegB(Mode.BYPASS)
    regd:RegD = RegD(Mode.BYPASS)
    rege:RegE = RegE(Mode.BYPASS)
    regf:RegF = RegF(Mode.BYPASS)

    def __call__(self):
        return self

    def op(self, alu:ALU_Op, signed:Signed=0):
        self.alu = alu
        self.signed = Bit(signed)
        return self

    def flag(self, op:Cond_Op):
        self.cond = op
        return self

    def reg(self, i, mode, data=0):
        if i == 0 or i == 'a':
            self.rega = RegA(mode)
            self.data0 = Data0(data)
        elif i == 1 or i == 'b':
            self.regb = RegB(mode)
            self.data1 = Data1(data)
        elif i == 3 or i == 'd':
            self.regd = RegD(mode)
            self.bit0 = Bit0(data)
        elif i == 4 or i == 'e':
            self.rege = RegE(mode)
            self.bit1 = Bit1(data)
        elif i == 5 or i == 'f':
            self.regf = RegF(mode)
            self.bit2 = Bit2(data)
        else:
            raise NotImplemented(i)
        return self

add = Inst().op(ALU_Op.Add)
sub = Inst().op(ALU_Op.Sub)

and_ = Inst().op(ALU_Op.And)
or_ = Inst().op(ALU_Op.Or)
xor = Inst().op(ALU_Op.XOr)

lsl = Inst().op(ALU_Op.SHL)
lsr = Inst().op(ALU_Op.SHR)
asr = Inst().op(ALU_Op.SHR, signed=1)

sel = Inst().op(ALU_Op.Sel)
abs = Inst().op(ALU_Op.Abs, signed=1)

umin = Inst().op(ALU_Op.LTE_Min)
umax = Inst().op(ALU_Op.GTE_Max)

smin = Inst().op(ALU_Op.LTE_Min, signed=1)
smax = Inst().op(ALU_Op.GTE_Max, signed=1)
