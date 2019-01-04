from dataclasses import dataclass
from .. import Bits, Enum, Product
from .cond import Cond
from .mode import Mode
from .lut import Bit, LUT

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

DATAWIDTH = 16
Data = Bits(DATAWIDTH)

RegA_Const = Bits(DATAWIDTH)
RegB_Const = Bits(DATAWIDTH)
RegD_Const = Bits(1)
RegE_Const = Bits(1)
RegF_Const = Bits(1)

RegA_Mode = Bits(2)
RegB_Mode = Bits(2)
RegD_Mode = Bits(2)
RegE_Mode = Bits(2)
RegF_Mode = Bits(2)

class ALU(Enum):
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

@dataclass
class Inst(Product):
    alu:ALU
    signed:Signed
    lut:LUT
    cond:Cond
    rega:RegA_Mode
    data0:RegA_Const
    regb:RegB_Mode
    data1:RegB_Const
    regd:RegD_Mode
    bit0:RegD_Const
    rege:RegE_Mode
    bit1:RegE_Const
    regf:RegF_Mode
    bit2:RegF_Const

