from peak.ir import IR
from peak import Peak, name_outputs
from hwtypes import BitVector as BV, Bit
from hwtypes.adt import Product

def gen_SmallIR(width):
    SmallIR = IR()

    class UnaryInput(Product):
        in0=BV[width]

    class Output(Product):
        out=BV[width]

    class BinaryInput(Product):
        in0=BV[width]
        in1=BV[width]

    SmallIR.add_peak_instruction("Add",BinaryInput,Output,lambda f, x, y: x+y)
    SmallIR.add_peak_instruction("Sub",BinaryInput,Output,lambda f, x, y: x-y)
    SmallIR.add_peak_instruction("And",BinaryInput,Output,lambda f, x, y: x&y)
    SmallIR.add_peak_instruction("Nand",BinaryInput,Output,lambda f, x, y: ~(x&y))
    SmallIR.add_peak_instruction("Or",BinaryInput,Output,lambda f, x, y: (x|y))
    SmallIR.add_peak_instruction("Nor",BinaryInput,Output,lambda f, x, y: ~(x|y))
    SmallIR.add_peak_instruction("Mul",BinaryInput,Output,lambda f, x, y: x*y)
    SmallIR.add_peak_instruction("Shftr",BinaryInput,Output,lambda f, x, y: x>>y)
    SmallIR.add_peak_instruction("Shftl",BinaryInput,Output,lambda f, x, y: x<<y)


    SmallIR.add_peak_instruction("Not",UnaryInput,Output,lambda f, x: ~x)
    SmallIR.add_peak_instruction("Neg",UnaryInput,Output,lambda f, x: -x)

    return SmallIR
