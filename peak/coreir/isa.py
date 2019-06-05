from peak.adt import Product, Sum, new_instruction, Enum
from hwtypes import BitVector, Bit
from peak import PeakNotImplementedError, PeakUnreachableError

WIDTH = 16
LOGWIDTH = 5
Data = BitVector[WIDTH]
LogData = BitVector[LOGWIDTH]

class BinaryOp(Enum):
    add = new_instruction()
    sub = new_instruction()
    and_ = new_instruction()
    or_ = new_instruction()
    xor = new_instruction()
    shl = new_instruction()
    lshr = new_instruction()
    ashr = new_instruction()
    mul = new_instruction()
    udiv = new_instruction()
    urem = new_instruction()
    sdiv = new_instruction()
    srem = new_instruction()
    smod = new_instruction()

def gen_BinarySemantics(family,width):
    BV = family.BitVector[width]
    class BinarySemantics(Peak):
        @name_outputs(out=BV)
        def __call__(self, op : BinaryOp, in0 : BV, in1 : BV):
            if op == BinaryOp.add:
                return in0 + in1
            elif op == BinaryOp.sub:
                return in0 - in1
            elif op == BinaryOp.and_:
                return in0 & in1
            elif op == BinaryOp.or_:
                return in0 | in1
            elif op == BinaryOp.xor:
                return in0 ^ in1
            elif op == BinaryOp.shl:
                return in0 << in1
            elif op == BinaryOp.lshr:
                return in0.as_uint() >> in1.as_uint()
            elif op == BinaryOp.ashr:
                return in0.as_sint() >> in1.as_sint()
            elif op == BinaryOp.mul:
                return in0 * in1
            elif op == BinaryOp.udiv:
                return in0 / in1
            elif op == BinaryOp.urem:
                raise PeakNotImplementedError()
            elif op == BinaryOp.sdiv:
                raise PeakNotImplementedError()
            elif op == BinaryOp.srem:
                raise PeakNotImplementedError()
            elif op == BinaryOp.smod:
                raise PeakNotImplementedError()
            else:
                raise Peak

class UnaryOp(Enum):
    wire = new_instruction()
    not_ = new_instruction()
    neg = new_instruction()

def gen_UnarySemantics(family,width):
    BV = family.BitVector[width]
    class UnarySemantics(Peak):
        @name_outputs(out=BV)
        def __call__(self, op : UnaryOp, in0 : BV):
            if op == UnaryOp.wire:
                return in0
            elif op == UnaryOp.not_:
                return ~in0
            elif op == UnaryOp.neg:
                return -in0
            else:
                raise PeakNotImplementedError()

class UnaryReduceOp(Enum):
    andr = new_instruction()
    orr = new_instruction()
    xorr = new_instruction()

def gen_UnaryReduceSemantics(family,width):
    BV = family.BitVector[width]
    Bit = family.Bit
    def reduce(fun):
        def _reduce(val):
            ret = val[0]
            for i in range(1,len(val)):
                ret = fun(ret,val[i])
        return _reduce
    class UnaryReduceSemantics(Peak):
        @name_outputs(out=family.Bit)
        def __call__(self, op : UnaryReduceOp, in0 : BV):
            if op == UnaryReduceOp.andr:
                return reduce(lambda a,b : a&b)(in0)
            elif op == UnaryReduceOp.orr:
                return reduce(lambda a,b : a|b)(in0)
            elif op == UnaryReduceOp.xorr:
                return reduce(lambda a,b : a^b)(in0)
            else:
                raise PeakUnreachableError()

class BinaryReduceOp(Enum):
    eq = new_instruction()
    neq = new_instruction()
    slt = new_instruction()
    sle = new_instruction()
    sgt = new_instruction()
    sge = new_instruction()
    ult = new_instruction()
    ule = new_instruction()
    ugt = new_instruction()
    uge = new_instruction()

def gen_BinaryReduceSemantics(family,width):
    BV = family.BitVector[width]
    Bit = family.Bit
    class BinaryReduceSemantics(Peak):
        @name_outputs(out=Bit)
        def __call__(self, op : BinaryReduceOp, in0 : BV, in1 : BV):
            sin0, sin1 = in0.as_sint(), in1.as_sint()
            uin0, uin1 = in0.as_uint(), in1.as_uint()
            if op == BinaryReduceOp.eq:
                return in0 == in1
            elif op == BinaryReduceOp.neq:
                return in0 != in1
            elif op == BinaryReduceOp.slt:
                return sin0 < sin1
            elif op == BinaryReduceOp.sle:
                return sin0 <= sin1
            elif op == BinaryReduceOp.sgt:
                return sin0 > sin1
            elif op == BinaryReduceOp.sge:
                return sin0 >= sin1
            elif op == BinaryReduceOp.ult:
                return uin0 < uin1
            elif op == BinaryReduceOp.ule:
                return uin0 <= uin1
            elif op == BinaryReduceOp.ugt:
                return uin0 > uin1
            elif op == BinaryReduceOp.uge:
                return uin0 >= uin1
            else:
                raise PeakUnreachableError()


#TODO missing:
# mux, const, slice, concat


class Const(Product):
    value : Data

class Slice(Product):
    lo : LogData
    hi : LogData

class Concat(Product):
    width0 : LogData
    width1 : LogData

class Inst(Sum[BinOp,UnaryOp,CompOp,Const,Slice,Concat]):
    pass
