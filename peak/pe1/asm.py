from .cond import Cond
from .mode import Mode
from .lut import Bit, LUT
from .isa import *

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

#
# Format a configuration of the PE - sets all fields
#
def inst(alu, signed=Signed.unsigned, lut=0, cond=Cond.Z,
    ra_mode=Mode.BYPASS, ra_const=0,
    rb_mode=Mode.BYPASS, rb_const=0,
    rd_mode=Mode.BYPASS, rd_const=0,
    re_mode=Mode.BYPASS, re_const=0,
    rf_mode=Mode.BYPASS, rf_const=0
    ):

    return Inst(alu, signed, LUT(lut), cond,
        RegA_Mode(ra_mode), RegA_Const(ra_const),
        RegB_Mode(rb_mode), RegB_Const(rb_const),
        RegD_Mode(rd_mode), RegD_Const(rd_const),
        RegE_Mode(re_mode), RegE_Const(re_const),
        RegF_Mode(rf_mode), RegF_Const(rf_const) )

# helper functions to format configurations

def add(ra_mode=Mode.BYPASS, rb_mode=Mode.BYPASS):
    return inst(ALU.Add, ra_mode=ra_mode, rb_mode=rb_mode)

def sub ():
    return inst(ALU.Sub)

def neg ():
    return inst(ALU.Sub)

def umult0 ():
    return inst(ALU.Mult0)

def umult1 ():
    return inst(ALU.Mult1)

def umult2 ():
    return inst(ALU.Mult2)

def smult0 ():
    return inst(ALU.Mult0, signed=Signed.signed)

def smult1 ():
    return inst(ALU.Mult1, signed=Signed.signed)

def smult2 ():
    return inst(ALU.Mult2, signed=Signed.signed)



def and_(ra_mode=Mode.BYPASS, rb_mode=Mode.BYPASS):
    return inst(ALU.And, ra_mode=ra_mode, rb_mode=rb_mode)

def or_(ra_mode=Mode.BYPASS, rb_mode=Mode.BYPASS):
    return inst(ALU.Or, ra_mode=ra_mode, rb_mode=rb_mode)

def xor(ra_mode=Mode.BYPASS, rb_mode=Mode.BYPASS):
    return inst(ALU.XOr, ra_mode=ra_mode, rb_mode=rb_mode)

def lsl():
    return inst(ALU.SHL)

def lsr():
    return inst(ALU.SHR)

def asr():
    return inst(ALU.SHR, signed=Signed.signed)

def sel():
    return inst(ALU.Sel)

def abs():
    return inst(ALU.Abs, signed=Signed.signed)

def umin():
    return inst(ALU.LTE_Min)

def umax():
    return inst(ALU.GTE_Max)

def smin():
    return inst(ALU.LTE_Min, signed=Signed.signed)

def smax():
    return inst(ALU.GTE_Max, signed=Signed.signed)

def eq():
    return inst(ALU.Sub, cond=Cond.Z)

def ne():
    return inst(ALU.Sub, cond=Cond.Z_n)

def ult():
    return inst(ALU.Sub, cond=Cond.ULT)

def ule():
    return inst(ALU.Sub, cond=Cond.ULE)

def ugt():
    return inst(ALU.Sub, cond=Cond.UGT)

def uge():
    return inst(ALU.Sub, cond=Cond.UGE)

def slt():
    return inst(ALU.Sub, cond=Cond.SLT)

def sle():
    return inst(ALU.Sub, cond=Cond.SLE)

def sgt():
    return inst(ALU.Sub, cond=Cond.SGT)

def sge():
    return inst(ALU.Sub, cond=Cond.SGE)

