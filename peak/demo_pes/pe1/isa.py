from hwtypes.adt import Product, Sum, new_instruction, Enum

DATAWIDTH = 16

class ALU_INST(Enum):
    Add  = new_instruction()
    And  = new_instruction()
    Xor  = new_instruction()
    Shft = new_instruction()

class INST(Product):
    ALU      = ALU_INST
