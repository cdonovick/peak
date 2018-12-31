from dataclasses import dataclass
from peak import Bits, Enum, Product, Sum
from .mode import Mode
from .lut import LUT
from .cond import Cond

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

NUM_INPUTS = 2
DATAWIDTH = 16

Bit = Bits(1)
Data = Bits(DATAWIDTH)

Data_Const = Bits(DATAWIDTH)
Data_Mode = Bits(2)

Bit0_Const = Bits(1)
Bit1_Const = Bits(1)
Bit2_Const = Bits(1)
Bit0_Mode = Bits(2)
Bit1_Mode = Bits(2)
Bit2_Mode = Bits(2)

@dataclass
class LUT(Product):
    bit0_mode:Bit0_Mode 
    bit0_const:Bit0_Const 
    bit1_mode:Bit1_Mode
    bit1_const:Bit1_Const
    bit2_mode:Bit2_Mode
    bit2_const:Bit2_Const 
    table:Bits(8) 

@dataclass
class _ALU(Product):
    data_modes:[Data_Mode]
    data_consts:[Data_Const]

class Add(_ALU):
  # returns res, res_p, C, V
  def eval(self, a, b, bit):
       return a+b, Bit(0), Bit(0), Bit(0)

class Sub(_ALU):
  def eval(self, a, b, bit):
       return a-b, Bit(0), Bit(0), Bit(0)

class And(_ALU):
  # returns res, res_p, C, V
  def eval(self, a, b, bit):
       return a&b, Bit(0), Bit(0), Bit(0)

class Or(_ALU):
  # returns res, res_p, C, V
  def eval(self, a, b, bit):
       return a|b, Bit(0), Bit(0), Bit(0)

class XOr(_ALU):
  # returns res, res_p, C, V
  def eval(self, a, b, bit):
       return a^b, Bit(0), Bit(0), Bit(0)

class ALU(Sum):
    fields = (Add, Sub, And, Or, XOr)

@dataclass
class Inst:
    alu:ALU
    lut:LUT
    cond:Cond

