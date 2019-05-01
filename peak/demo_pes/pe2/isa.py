from hwtypes.adt import Product, Sum, new_instruction, Enum

DATAWIDTH = 16

class ALU_INST(Enum):
    Add  = new_instruction()
    And  = new_instruction()
    Shft = new_instruction()
    Xor  = new_instruction()

class FLAG_INST(Enum):
    C = new_instruction()
    Z = new_instruction()

class INST(Product):
    ALU      = ALU_INST
    FLAG     = FLAG_INST
