from peak.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector

class Primitive(Enum):
    add = new_instruction()
    mul = new_instruction()
    sub = new_instruction()
    or_ = new_instruction()
    and_ = new_instruction()
    shl = new_instruction()
    lshr = new_instruction()
    not_ = new_instruction()
    neg = new_instruction()
    eq = new_instruction()
    neq = new_instruction()
    ult = new_instruction()
    ule = new_instruction()
    ugt = new_instruction()
    uge = new_instruction()
    xor = new_instruction()
    const = new_instruction()

def gen_inst_type(family, width=16):
    Data = family.BitVector[width]
    class Inst(Product):
        primitive : Primitive
        const_value : Data

    return Inst
