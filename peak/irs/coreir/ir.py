from peak.ir import IR
from hwtypes import BitVector, Bit
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

    def add_binary(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            class Binary(Peak):
                @name_outputs(out=Data)
                def __call__(self,in0 : Data, in1 : Data):
                    return fun(in0,in1)
            Binary.__name__ = name
            return Binary
        CoreIR.add_instruction(name,family_closure)
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
        add_binary(name,fun)

    def add_unary(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            class Unary(Peak):
                @name_outputs(out=Data)
                def __call__(self,in_ : Data):
                    return fun(in_)
            Unary.__name__ = name
            return Unary
        CoreIR.add_instruction(name,family_closure)

    for name,fun in (
        ("wire",lambda x: x),
        ("not_",lambda x: ~x),
        ("neg",lambda x: -x)
    ):
        add_unary(name,fun)

    def add_unary_reduce(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            Bit = family.Bit
            class UnaryReduce(Peak):
                @name_outputs(out=Bit)
                def __call__(self,in_ : Data):
                    return fun(in_)
            UnaryReduce.__name__ = name
            return UnaryReduce
        CoreIR.add_instruction(name,family_closure)

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
        add_unary_reduce(name,fun)

    def add_binary_reduce(name,fun):
        def family_closure(family):
            Data = family.BitVector[width]
            Bit = family.Bit
            class BinaryReduce(Peak):
                @name_outputs(out=Bit)
                def __call__(self,in0 : Data, in1 : Data):
                    return fun(in0,in1)
            BinaryReduce.__name__ = name
            return BinaryReduce
        CoreIR.add_instruction(name,family_closure)
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
        add_binary_reduce(name,fun)

    def mux_family_closure(family):
        Data = family.BitVector[width]
        Bit = family.Bit
        class mux(Peak):
            @name_outputs(out=Data)
            def __call__(self,in0 : Data, in1 : Data, sel : Bit):
                return sel.ite(in1,in0)
        return mux
    CoreIR.add_instruction("mux",mux_family_closure)

    return CoreIR

#TODO missing:
# slice, concat, sext, zext
