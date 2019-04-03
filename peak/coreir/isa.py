from peak.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector, Bit

WIDTH = 16
LOGWIDTH = 5
Data = BitVector[WIDTH]
LogData = BitVector[LOGWIDTH]

class BinaryOp(Enum):
    add = new_instruction()
    mul = new_instruction()
    sub = new_instruction()
    or_ = new_instruction()
    and_ = new_instruction()
    shl = new_instruction()
    lshr = new_instruction()
    xor = new_instruction()

class UnaryOp(Enum):
    not_ = new_instruction()
    neg = new_instruction()

class CompOp(Enum):
    eq = new_instruction()
    neq = new_instruction()
    ult = new_instruction()
    ule = new_instruction()
    ugt = new_instruction()
    uge = new_instruction()

class Const(Product):
    value : Data

class Slice(Product):
    lo : LogData
    hi : LogData

class Concat(Product):
    width0 : LogData
    width1 : LogData

class Inst(Sum[BinOp,UnaryOp,CompOp,Const,Slice,Concat]):
    pass
