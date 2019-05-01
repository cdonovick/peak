from hwtypes.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector

Datawidth = 16
Data = BitVector[Datawidth]

class ALUOP(Enum):
    Add = new_instruction()
    Sub = new_instruction()
    Or =  new_instruction()
    And = new_instruction()
    XOr = new_instruction()

class Inst(Product):
    alu_op = ALUOP
