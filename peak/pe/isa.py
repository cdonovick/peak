from dataclasses import dataclass
from peak import Bits, Enum

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

DATAWIDTH = 16

Bit = Bits(1)
Data = Bits(DATAWIDTH)

class Mode(Enum):
    CONST = 0
    VALID = 1
    BYPASS = 2
    DELAY = 3

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

Signed = Bit

class Cond_Op(Enum):
    Z = 0
    Z_n = 1
    C = 2
    C_n = 3
    N = 4
    N_n = 5
    V = 6
    V_n = 7
    Hi = 8
    Ls = 9
    GE = 10
    LT = 11
    GT = 12
    LE = 13
    LUT = 14
    PE = 15

LUT_Op = Bits(8)

@dataclass
class Inst:
    signed:Signed = Bit(0)
    alu:ALU_Op = ALU_Op.Add
    lut:LUT_Op = LUT_Op(0)
    cond:Cond_Op = Cond_Op.Z
    data0:Data = Data(0)
    data1:Data = Data(0)
    data2:Data = Data(0)
    bit0:Bit = Bit(0)
    bit1:Bit = Bit(0)
    bit2:Bit = Bit(0)
    rega:Mode = Mode.BYPASS
    regb:Mode = Mode.BYPASS
    regc:Mode = Mode.BYPASS
    regd:Mode = Mode.BYPASS
    rege:Mode = Mode.BYPASS
    regf:Mode = Mode.BYPASS

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
        if i == 0:
            self.rega = mode
            self.data0 = Data(data)
        elif i == 1:
            self.regb = mode
            self.data1 = Data(data)
        elif i == 2:
            self.regc = mode
            self.data2 = Data(data)
        elif i == 3:
            self.regd = mode
            self.bit0 = Bit(data)
        elif i == 4:
            self.rege = mode
            self.bit1 = Bit(data)
        elif i == 5:
            self.regf = mode
            self.bit2 = Bit(data)
        else:
            raise NotImplemented(i)
        return self

add = Inst().op(ALU_Op.Add)
sub = Inst().op(ALU_Op.Sub)

and_ = Inst().op(ALU_Op.And)
or_ = Inst().op(ALU_Op.Or)
xor = Inst().op(ALU_Op.XOr)

