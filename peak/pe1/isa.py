from dataclasses import dataclass
from .. import Bits, Enum, Product
from .cond import Cond
from .mode import Mode
from .lut import Bit, LUT

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

# Current PE has 16-bit data path
DATAWIDTH = 16
Data = Bits(DATAWIDTH)

# Constant values for registers
RegA_Const = Bits(DATAWIDTH)
RegB_Const = Bits(DATAWIDTH)
RegD_Const = Bits(1)
RegE_Const = Bits(1)
RegF_Const = Bits(1)

# Modes for registers
RegA_Mode = Mode
RegB_Mode = Mode
RegD_Mode = Mode
RegE_Mode = Mode
RegF_Mode = Mode

# ALU operations
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

# Whether the operation is unsigned (0) or signed (1)
Signed = Bits(1)

#
# Each configuration is given by the following fields
#
@dataclass
class Inst(Product):
    alu:ALU          # ALU operation
    signed:Signed    # unsigned or signed 
    lut:LUT          # LUT operation as a 3-bit LUT
    cond:Cond        # Condition code (see cond.py)
    rega:RegA_Mode   # RegA mode (see mode.py)
    data0:RegA_Const # RegA constant (16-bits)
    regb:RegB_Mode   # RegB mode
    data1:RegB_Const # RegB constant (16-bits)
    regd:RegD_Mode   # RegD mode
    bit0:RegD_Const  # RegD constant (1-bit)
    rege:RegE_Mode   # RegE mode
    bit1:RegE_Const  # RegE constant (1-bit)
    regf:RegF_Mode   # RegF mode
    bit2:RegF_Const  # RegF constant (1-bit)

