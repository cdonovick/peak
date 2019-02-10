from ..isa_builder import Product, Union, new_inst, product

DATAWIDTH = 16

class ALU_INST(Union):
    Add = new_inst()
    Neg = new_inst()
    And = new_inst()
    Or  = new_inst()
    Not = new_inst()

class FLAG_INST(Union):
    C = new_inst()
    Z = new_inst()

@product
class INST(Product):
    ALU  : ALU_INST
    FLAG : FLAG_INST


