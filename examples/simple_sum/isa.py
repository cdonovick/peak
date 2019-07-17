from hwtypes.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector

Datawidth = 16
Data = BitVector[Datawidth]

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

Instr = Sum[Add,Sub,Add1]
