from hwtypes.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector
from hwtypes.modifiers import make_modifier

#This is an isa to test products within sums within products
#This causes a lot of complex bindings to occur

def from_product(name, product):
    return Product.from_fields(name,product.field_dict)

def gen_isa(width):
    Data =BitVector[width]

    class BinaryOpKind(Product):
        in0 = Data
        in1 = Data

    Add = from_product("Add",BinaryOpKind)
    Sub = from_product("Sub",BinaryOpKind)

    class UnaryOpKind(Product):
        in0 = Data

    Add1 = from_product("Add1",UnaryOpKind)

    #This will indicate whether to use inputs from the instruction
    #or inputs from the sim (creating lots of possible bindings)
    class WhichInputs(Enum):
        Sim=0
        Instr=1

    Op = Sum[Add,Sub,Add1]

    class Instr(Product):
        op=Op
        which_inputs=WhichInputs
    return Instr
