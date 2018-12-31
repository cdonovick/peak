from dataclasses import dataclass
from .. import Bits, Enum, Product
from .cond import Cond
from .mode import Mode
from .lut import Bit, LUT

# https://github.com/StanfordAHA/CGRAGenerator/wiki/PE-Spec

def inst(alu, signed=0, lut=0, cond=Cond.Z,
    ra_mode=Mode.Bypass, rb_mode, rc_mode, rd_mode, re_mode, rf_mode,
    ra_const, rb_const, rc_const, rd_const, re_const, rf_const):

    return Inst(ALU(alu), Signed(signed), LUT(lut), Cond(cond),
        RegA_Mode(ra_mode), RegB_Mode(rb_mode), RegC_Mode(rc_mode),
        RegD_Mode(rd_mode), RegE_Mode(re_mode), RegF_Mode(rf_mode),
        RegA_Const(ra_const), RegB_Const(rb_const), RegC_Const(rc_const),
        RegD_Const(rd_const), RegE_Const(re_const), RegF_Const(rf_const) )

def add():
    return inst(ALU.Add)

sub = Inst().op(ALU_Op.Sub)

and_ = Inst().op(ALU_Op.And)
or_ = Inst().op(ALU_Op.Or)
xor = Inst().op(ALU_Op.XOr)

lsl = Inst().op(ALU_Op.SHL)
lsr = Inst().op(ALU_Op.SHR)
asr = Inst().op(ALU_Op.SHR, signed=1)

sel = Inst().op(ALU_Op.Sel)
abs = Inst().op(ALU_Op.Abs, signed=1)

umin = Inst().op(ALU_Op.LTE_Min)
umax = Inst().op(ALU_Op.GTE_Max)

smin = Inst().op(ALU_Op.LTE_Min, signed=1)
smax = Inst().op(ALU_Op.GTE_Max, signed=1)
