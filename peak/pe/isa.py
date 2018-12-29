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
Bit0 = Bits(1)
Bit1 = Bits(1)
Bit2 = Bits(1)

Data_Mode = Bits(2)
Bit0_Mode = Bits(2)
Bit1_Mode = Bits(2)
Bit2_Mode = Bits(2)

@dataclass
class BaseInst(Product):
    data = [Data(0) for i in range(NUM_INPUTS)]
    data_mode = [Data_Mode(Mode.BYPASS) for i in range(NUM_INPUTS)]

    lut:LUT = LUT(0)
    bit0:Bit0 = Bit0(0)
    bit1:Bit1 = Bit1(0)
    bit2:Bit2 = Bit2(0)
    bit0_mode:Bit0_Mode = Bit0_Mode(Mode.BYPASS)
    bit1_mode:Bit1_Mode = Bit1_Mode(Mode.BYPASS)
    bit2_mode:Bit2_Mode = Bit2_Mode(Mode.BYPASS)

    cond:Cond = Cond.Z

    def __call__(self):
        return self

    def reg(self, i, mode, data=0):
        if isinstance(i, int):
            self.data_mode[i] = Data_Mode(mode)
            self.data[i] = Data(data)
        elif i == 'bit0':
            self.bit0_mode = Bit0_Mode(mode)
            self.bit0 = Bit0(data)
        elif i == 'bit1':
            self.bit1_mode = Bit1_Mode(mode)
            self.bit1 = Bit1(data)
        elif  i == 'bit2':
            self.bit2_mode = Bit2_Mode(mode)
            self.bit2 = Bit2(data)
        else:
            raise NotImplemented(i)
        return self

    def flag(self, cond:Cond):
        self.cond = cond
        return self

class Add(BaseInst):
  def eval(self, a, b, bit):
       return a+b, Bit(0), Bit(0), Bit(0)

class Sub(BaseInst):
  def eval(self, a, b, bit):
       return a-b, Bit(0), Bit(0), Bit(0)

class Inst(Sum):
    fields = (Add, Sub)

