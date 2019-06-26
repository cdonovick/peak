from hwtypes import BitVector, Bit

from hwtypes.adt import Enum, Product, Sum, Tuple
from .mode import Mode
from .lut import LUT_t
from .cond import Cond

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

NUM_INPUTS = 2
DATAWIDTH = 16

Data = BitVector[DATAWIDTH]

Data_Const = Data
Data_Mode = Mode

Bit0_Const = Bit
Bit1_Const = Bit
Bit2_Const = Bit
Bit0_Mode = Mode
Bit1_Mode = Mode
Bit2_Mode = Mode

class LUT(Product):
    bit0_mode=Bit0_Mode
    bit0_const=Bit0_Const
    bit1_mode=Bit1_Mode
    bit1_const=Bit1_Const
    bit2_mode=Bit2_Mode
    bit2_const=Bit2_Const
    table=LUT_t

class _ALU(Product):
    data_modes  = Tuple[(Data_Mode for _ in range(NUM_INPUTS))]
    data_consts = Tuple[(Data_Const for _ in range(NUM_INPUTS))]

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

ALU = Sum[Add, Sub, And, Or, XOr]

class Inst(Product):
    alu=ALU
    lut=LUT
    cond=Cond

