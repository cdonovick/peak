from peak.ir import IR
from peak import Peak, name_outputs
from hwtypes import BitVector
from hwtypes.adt import Enum

def gen_SmallIR(width):
    SmallIR = IR()
    def add_binary(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            class Binary(Peak):
                @name_outputs(out=Data)
                def __call__(self,in0 : Data, in1 : Data):
                    return fun(in0,in1)
            Binary.__name__ = name
            return Binary
        SmallIR.add_instruction(name,family_closure)
    for name,fun in (
        ("Add",lambda x,y: x+y),
        ("Sub",lambda x,y: x-y),
        ("And",lambda x,y: x&y)
    ):
        add_binary(name,fun)

    def add_unary(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            class Unary(Peak):
                @name_outputs(out=Data)
                def __call__(self,in0 : Data):
                    return fun(in0)
            Unary.__name__ = name
            return Unary
        SmallIR.add_instruction(name,family_closure)

    for name,fun in (
        ("Not",lambda x: ~x),
        ("Neg",lambda x: -x)
    ):
        add_unary(name,fun)

    return SmallIR
