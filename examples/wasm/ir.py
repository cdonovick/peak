from peak.ir import IR
from peak import Peak, name_outputs
from hwtypes import BitVector, Bit
from hwtypes.adt import Product
import math

WASM = IR()

class Output32(Product):
    out=BitVector[32]

class Input32(Product):
    in0=BitVector[32]

class Output64(Product):
    out=BitVector[64]

class Input64(Product):
    in0=BitVector[64]

def gen_integer(width):
    prefix = f"i{width}"
    logwidth = int(math.log2(width))
    Data = BitVector[width]
    Data32 = BitVector[32]

    #TODO is this a problem declaring a constant outside the scope?
    def shift_amount(x : Data):
        #Need to zero out all but the bottom bits
        mask = Data(width)-Data(1)
        return x & mask

    assert width in (32,64)

    class UnaryInput(Product):
        in0=Data

    class Output(Product):
        out=Data

    class BinaryInput(Product):
        in0=Data
        in1=Data

    #Integer Arithmetic Instructions
    WASM.add_peak_instruction(f"{prefix}_add",BinaryInput,Output,lambda x,y: x+y)
    WASM.add_peak_instruction(f"{prefix}_sub",BinaryInput,Output,lambda x,y: x-y)
    WASM.add_peak_instruction(f"{prefix}_mul",BinaryInput,Output,lambda x,y: x*y)
    WASM.add_peak_instruction(f"{prefix}_div_s",BinaryInput,Output,lambda x,y: x.bvsdiv(y))
    WASM.add_peak_instruction(f"{prefix}_div_u",BinaryInput,Output,lambda x,y: x.bvudiv(y))
    WASM.add_peak_instruction(f"{prefix}_rem_s",BinaryInput,Output,lambda x,y: x.bvsrem(y))
    WASM.add_peak_instruction(f"{prefix}_rem_u",BinaryInput,Output,lambda x,y: x.bvurem(y))
    WASM.add_peak_instruction(f"{prefix}_and",BinaryInput,Output,lambda x,y: x & y)
    WASM.add_peak_instruction(f"{prefix}_or",BinaryInput,Output,lambda x,y: x | y)
    WASM.add_peak_instruction(f"{prefix}_xor",BinaryInput,Output,lambda x,y: x ^ y)
    WASM.add_peak_instruction(f"{prefix}_shl",BinaryInput,Output,lambda x,y: x << shift_amount(y))
    WASM.add_peak_instruction(f"{prefix}_shr_s",BinaryInput,Output,lambda x,y: x.bvashr(shift_amount(y)))
    WASM.add_peak_instruction(f"{prefix}_shr_l",BinaryInput,Output,lambda x,y: x.bvlshr(shift_amount(y)))

    #Need to test these
    def rotl(in0 : Data, in1 : Data):
        in1 = shift_amount(in1)
        msbs = (in0 << in1)
        lsbs = in0.bvlshr(Data(32)-in1)
        return msbs | lsbs
    WASM.add_peak_instruction(f"{prefix}_rotl",BinaryInput,Output,rotl)

    def rotr(in0 : Data, in1 : Data):
        in1 = shift_amount(in1)
        msbs = (in0 << (Data32-in1))
        lsbs = in0.bvlshr(in1)
        return msbs | lsbs
    WASM.add_peak_instruction(f"{prefix}_rotr",BinaryInput,Output,rotr)

    def clz(in0 : Data):
        #TODO
        return Data(0)
    WASM.add_peak_instruction(f"{prefix}_clz",UnaryInput,Output,clz)

    def ctz(in0 : Data):
        #TODO
        return Data(0)
    WASM.add_peak_instruction(f"{prefix}_ctz",UnaryInput,Output,ctz)

    def popcnt(in0 : Data):
        #TODO
        return Data(0)
    WASM.add_peak_instruction(f"{prefix}_popcnt",UnaryInput,Output,popcnt)

    WASM.add_peak_instruction(f"{prefix}_eqz",UnaryInput,Output32,lambda x : x==Data(0))

    def to32(bit : Bit):
        assert isinstance(bit,Bit)
        return bit.ite(Data32(1),Data32(0))

    #Integer Comparison Instructions
    WASM.add_peak_instruction(f"{prefix}_eq",BinaryInput,Output32,lambda x : to32(x==y))
    WASM.add_peak_instruction(f"{prefix}_ne",BinaryInput,Output32,lambda x : to32(x!=y))
    WASM.add_peak_instruction(f"{prefix}_lt_s",BinaryInput,Output32,lambda x : to32(x.bvslt(y)))
    WASM.add_peak_instruction(f"{prefix}_lt_u",BinaryInput,Output32,lambda x : to32(x.bvslt(y)))
    WASM.add_peak_instruction(f"{prefix}_le_s",BinaryInput,Output32,lambda x : to32(x.bvsle(y)))
    WASM.add_peak_instruction(f"{prefix}_le_u",BinaryInput,Output32,lambda x : to32(x.bvule(y)))
    WASM.add_peak_instruction(f"{prefix}_gt_s",BinaryInput,Output32,lambda x : to32(x.bvsgt(y)))
    WASM.add_peak_instruction(f"{prefix}_gt_u",BinaryInput,Output32,lambda x : to32(x.bvugt(y)))
    WASM.add_peak_instruction(f"{prefix}_ge_s",BinaryInput,Output32,lambda x : to32(x.bvsge(y)))
    WASM.add_peak_instruction(f"{prefix}_ge_u",BinaryInput,Output32,lambda x : to32(x.bvuge(y)))


gen_integer(32)
gen_integer(64)

#Conversion ops

WASM.add_peak_instruction("i32_wrap", Input64,Output32, lambda x : x[:32])
WASM.add_peak_instruction("i64_extend_s", Input32,Output64, lambda x: x.sext(32))
WASM.add_peak_instruction("i64_extend_u", Input32,Output64, lambda x: x.zext(32))


for name, inst in WASM.instructions.items():
    print(name,inst)

