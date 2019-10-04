import typing as  tp
import operator
from hwtypes.adt import Product, Sum, new_instruction, Enum
from hwtypes import TypeFamily
from peak import name_outputs, Peak

WIDTH = 16

def gen_pe(num_alus : int, num_inputs : int, family : TypeFamily):
    assert num_alus == 1
    assert num_inputs < 16

    Bit = family.Bit
    Nibble = family.BitVector[4]
    Word = family.BitVector[WIDTH]

    class Op(Enum):
        Add = new_instruction()
        And = new_instruction()
        Mul = new_instruction()

    class ALU(Product):
        op = Op
        in0 = Nibble
        in1 = Nibble

    class Inst(Product):
        alu = ALU

    class PE(Peak):
        @name_outputs(res=Word)
        def __call__(self, inst : Inst, inputs : tp.List[Word]):
            def alu(inst : ALU, inputs : tp.List[Word]):
                in0 = inputs[int(inst.in0)]
                in1 = inputs[int(inst.in1)]
                if   inst.op == Op.Add:
                    res = in0 + in1
                elif inst.op == Op.And:
                    res = in0 & in1
                elif inst.op == Op.Mul:
                    res = in0 * in1
                else:
                    raise TypeError()

                return res
            res = alu(inst.alu, inputs)
            return res

    return Bit, Nibble, Word, Inst, ALU, Op, PE
