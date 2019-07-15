from peak.ir import IR
from hwtypes import AbstractBitVector, AbstractBit
from hwtypes.adt import Product
from peak import Peak, name_outputs

def gen_CoreIR(width):
    CoreIR = IR()
    def const_family_closure(family):
        Data = family.BitVector[width]
        class ConstModParams(Product):
            value_=Data

        class const(Peak):
            @name_outputs(out=Data)
            def __call__(self,modparams : ConstModParams):
                return modparams.value
        return const
    CoreIR.add_instruction("const",const_family_closure)

    class UnaryInput(Product):
        in0=AbstractBitVector[width]

    class BinaryInput(Product):
        in0=AbstractBitVector[width]
        in1=AbstractBitVector[width]

    class TernaryInput(Product):
        in0=AbstractBitVector[width]
        in1=AbstractBitVector[width]
        sel=AbstractBit

    class OutputBV(Product):
        out=AbstractBitVector[width]

    class OutputBit(Product):
        out=AbstractBit

    for name,fun in (
        ("add",lambda x,y: x+y),
        ("sub",lambda x,y: x-y),
        ("and_",lambda x,y: x&y),
        ("or_",lambda x,y: x|y),
        ("xor",lambda x,y: x^y),
        ("shl",lambda x,y: x<<y),
        ("lshr",lambda x,y: x.bvlshr(y)),
        ("ashr",lambda x,y: x.bvashr(y)),
        ("mul",lambda x,y: x*y),
        #("udiv",lambda x,y: x.bvudiv(y)),
        #("urem",lambda x,y: x.bvurem(y)),
        #("sdiv",lambda x,y: x.bvsdiv(y)),
        #("srem",lambda x,y: x.bvsrem(y)),
        #("smod",lambda x,y: x.bvsmod(y)),
    ):
        CoreIR.add_peak_instruction(name,BinaryInput,OutputBV,fun)

    for name,fun in (
        ("wire",lambda x: x),
        ("not_",lambda x: ~x),
        ("neg",lambda x: -x)
    ):
        CoreIR.add_peak_instruction(name,UnaryInput,OutputBV,fun)

    def reduce(fun):
        def _reduce(val):
            ret = val[0]
            for i in range(1,len(val)):
                ret = fun(ret,val[i])
            return ret
        return _reduce

    for name,fun in (
        ("andr",lambda x: reduce(lambda a,b : a&b)(x)),
        ("orr",lambda x: reduce(lambda a,b : a|b)(x)),
        ("xorr",lambda x: reduce(lambda a,b : a^b)(x)),
    ):
        CoreIR.add_peak_instruction(name,UnaryInput,OutputBit,fun)

    for name, fun in (
        ("eq" ,lambda x,y: x==y),
        ("neq",lambda x,y: x!=y),
        ("slt",lambda x,y: x.bvslt(y)),
        ("sle",lambda x,y: x.bvsle(y)),
        ("sgt",lambda x,y: x.bvsgt(y)),
        ("sge",lambda x,y: x.bvsge(y)),
        ("ult",lambda x,y: x.bvult(y)),
        ("ule",lambda x,y: x.bvule(y)),
        ("ugt",lambda x,y: x.bvugt(y)),
        ("uge",lambda x,y: x.bvuge(y)),
    ):
        CoreIR.add_peak_instruction(name,BinaryInput,OutputBit,fun)

    #add mux
    CoreIR.add_peak_instruction("mux",TernaryInput,OutputBV,lambda in0,in1,sel: sel.ite(in1,in0))

    return CoreIR

#TODO missing:
# slice, concat, sext, zext
