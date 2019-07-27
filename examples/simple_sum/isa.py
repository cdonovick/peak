from hwtypes.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector

#This is an isa to test products within sums within products
#This causes a lot of complex bindings to occur
def gen_isa(width):
    Data =BitVector[width]

    class BinaryOpKind(Product):
        in0 = Data
        in1 = Data

    class Add(BinaryOpKind):
        pass

    class Sub(BinaryOpKind):
        pass

    class UnaryOpKind(Product):
        in0 = Data

    class Add1(UnaryOpKind):
        pass

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
