from .. import Peak, name_outputs
import typing as tp
from .isa import *
from hwtypes import TypeFamily

def gen_coreir(family : TypeFamily, width=16):
    Data = family.BitVector[width]
    Bit = family.Bit
    Inst = gen_inst_type(family, width)

    class CoreIR(Peak):
        
        @name_outputs(out=Data,out_b=Bit)
        def __call__(self, inst : Inst, in0 : Data, in1 : Data):
            primitive = inst.primitive
            const_value = inst.const_value

            res = Data(0)
            res_b = Bit(0)
            if primitive == Primitive.add:
                res = in0 + in1
            elif primitive == Primitive.mul:
                res = in0 * in1
            elif primitive == Primitive.sub:
                res = in0 - in1
            elif primitive == Primitive.or_:
                res = in0 | in1
            elif primitive == Primitive.and_:
                res = in0 & in1
            elif primitive == Primitive.shl:
                res = in0 << in1
            elif primitive == Primitive.lshr:
                res = in0 >> in1
            elif primitive == Primitive.not_:
                res = ~in0
            elif primitive == Primitive.neg:
                res = -in0
            elif primitive == Primitive.eq:
                res_b = (in0 == in1)
            elif primitive == Primitive.neq:
                res = (in0 !=in1)
            elif primitive == Primitive.ult:
                res = in0 < in1
            elif primitive == Primitive.ule:
                res = in0 <= in1
            elif primitive == Primitive.ugt:
                res = in0 > in1
            elif primitive == Primitive.uge:
                res = in0 >= in1
            elif primitive == Primitive.xor:
                res = in0 ^ in1
            elif primitive == Primitive.const:
                res = const_value
            else:
                raise NotImplementedError

            return res, res_b
    
    return CoreIR
