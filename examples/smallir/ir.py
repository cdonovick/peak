from peak.ir import IR
from peak import Peak, name_outputs
from hwtypes import BitVector
from hwtypes.adt import Product

def gen_SmallIR(width):
    SmallIR = IR()

    class UnaryInput(Product):
        in0=BitVector[width]

    class Output(Product):
        out=BitVector[width]

    class BinaryInput(Product):
        in0=BitVector[width]
        in1=BitVector[width]

    SmallIR.add_peak_instruction("Add",BinaryInput,Output,lambda x,y: x+y)
    SmallIR.add_peak_instruction("Sub",BinaryInput,Output,lambda x,y: x-y)
    SmallIR.add_peak_instruction("And",BinaryInput,Output,lambda x,y: x&y)

    SmallIR.add_peak_instruction("Not",UnaryInput,Output,lambda x: ~x)
    SmallIR.add_peak_instruction("Neg",UnaryInput,Output,lambda x: -x)


    return SmallIR
