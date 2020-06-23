from .isa import Op
from peak import Peak, family_closure
import magma
from hwtypes import SMTFPVector, FPVector, RoundingMode
from peak.family import MagmaFamily, SMTFamily
from ast_tools.passes import begin_rewrite, end_rewrite, if_inline
from ast_tools.macros import inline

def BFloat16_fc(family):
    if isinstance(family, MagmaFamily):
        BFloat16 =  magma.BFloat[16]
        BFloat16.reinterpret_from_bv = lambda bv: BFloat16(bv)
        BFloat16.reinterpret_as_bv = lambda f: magma.Bits[16](f)
        return BFloat16
    elif isinstance(family, SMTFamily):
        FPV = SMTFPVector
    else:
        FPV = FPVector
    BFloat16 = FPV[8, 7, RoundingMode.RNE, False]
    return BFloat16

@family_closure
def ALU_fc(family):
    Bit = family.Bit
    Data = family.BitVector[16]
    SData = family.Signed[16]


    @family.assemble(locals(), globals())
    class ALU(Peak):
        def __call__(self, inst : Op, data0 : Data, data1 : Data, fp_unit : fp_unit_fc(family)) -> Data:
            if inst == Op.Add:
                res = data0 + data1
            elif inst == Op.And:
                res = data0 & data1
            elif inst == Op.Xor:
                res = data0 ^ data1
            elif inst == Op.Shft:
                res = data0.bvshl(data1)
            else :
                res = fp_unit(inst, data0, data1)
            return res

    return ALU


@family_closure
def fp_unit_fc(family):
   
    Data = family.BitVector[16]
   
    BFloat16 = BFloat16_fc(family)
    FPExpBV = family.BitVector[8]
    FPFracBV = family.BitVector[7]

    def bv2float(bv):
        return BFloat16.reinterpret_from_bv(bv)

    def float2bv(bvf):
        return BFloat16.reinterpret_as_bv(bvf)

    @family.assemble(locals(), globals())
    class fp_unit(Peak):

        def __init__(self):
            self.ret : Data = Data(0)

        @end_rewrite()
        @if_inline()
        @begin_rewrite()
        def __call__(self, inst : Op, data0 : Data, data1 : Data) -> Data:
        
            if inline(not isinstance(family, SMTFamily)):
                if inst == Op.FP_sub:
                    data1 = (Data(1) << (16-1)) ^ data1
                a_fpadd = bv2float(data0)
                b_fpadd = bv2float(data1)
                self.ret = float2bv(a_fpadd + b_fpadd)

            return self.ret

        def _set_fp(self, fp_val : Data):
            self.ret = fp_val

    return fp_unit
