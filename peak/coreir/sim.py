from .. import Peak, name_outputs
import typing as tp
from .isa import *
from hwtypes import TypeFamily

class CoreIR(Peak):
    def __call__(self, inst : Inst, in0 : Data, in1 : Data):

def binary_op(inst, in0 : Data, in1 : Data):
    if inst == BinaryOp.add:
        res = in0 + in1
    elif inst == BinaryOp.mul:
        res = in0 * in1
    elif inst == BinaryOp.sub:
        res = in0 - in1
    elif inst == BinaryOp.or_:
        res = in0 | in1
    elif inst == BinaryOp.and_:
        res = in0 & in1
    elif inst == BinaryOp.shl:
        res = in0 << in1
    elif inst == BinaryOp.lshr:
        res = in0 >> in1
    else:
        raise NotImplementedError
    return res

def unary_op(inst, in_ : Data):
    if inst == UnaryOp.not_:
        res = ~in0
    elif inst == UnaryOp.neg:
        res = -in0
    else:
        raise NotImplementedError
    return res

def comp_op(inst, in0 : Data, in1 : Data):

    if inst == CompOp.eq:
        res_b = in0 == in1
    elif inst == CompOp.neq:
        res_b = in0 != in1 
    elif inst == CompOp.ult:
        res_b = in0 < in1 
    elif inst == CompOp.ule:
        res_b = in0 <= in1 
    elif inst == CompOp.ugt:
        res_b = in0 > in1 
    elif inst == CompOp.uge:
        res_b = in0 >= in1 
    else:
        raise NotImplementedError
    return res_b

def mask(size):
    return (Data(1)<<size)-Data(1)

class CoreIR(Peak):

    def __call__(self, inst : Inst, in0 : Data, in1 : Data):
        kind, inst = inst.match()

        res = Data(0)
        res_b = Bit(0)
        if kind==BinaryOp:
            res = binary_op(inst,in0,in1)
        elif kind==UnaryOp:
            res = unary_op(inst,in0)
        elif kind==CompOp:
            res_b = comp_op(inst,in0,in1)
        elif kind==Const:
            res = inst.value
        elif kind==Slice:
            res = (in0 >> inst.lo) & mask(inst.hi-inst.lo)
        elif kind ==Concat:
            res = in0 | (in1<<inst.width0)

        return res, res_b
