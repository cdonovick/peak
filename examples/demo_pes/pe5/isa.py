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

class INVERTER_INST(Enum):
    Ident  = new_instruction()
    Invert = new_instruction()

class BIT_CONSTANT(Enum):
    Zero = 0
    One  = 1

class INST(Product):
    ALU      = ALU_INST
    FLAG     = FLAG_INST
    INVERTER = INVERTER_INST
    BIT      = BIT_CONSTANT
