from functools import lru_cache
from types import SimpleNamespace

from peak import family_closure, Peak
from peak.family import SMTFamily, MagmaFamily
from hwtypes import SMTFPVector, FPVector, RoundingMode as RM, TypeFamily
from peak.black_box import BlackBox
from hwtypes import BitVector, Bit
from hwtypes.adt import Enum
import magma

class RoundingMode(Enum):
    RNE = 0
    RTZ = 1
    RDN = 2
    RUP = 3
    RMM = 4

def RoudningMode_utils(family):
    RM = RoundingMode
    RM_c = family.get_constructor(RoundingMode)
    BV3 = lambda e: family.BitVector[3](e.value)
    def from_rm(rm: RoundingMode) -> BitVector[3]:
        return (rm==RM.RNE).ite(
            BV3(RM.RNE),
            (rm==RM.RTZ).ite(
                BV3(RM.RTZ),
                (rm == RM.RDN).ite(
                    BV3(RM.RDN),
                    (rm == RM.RUP).ite(
                        BV3(RM.RUP),
                        BV3(RM.RMM),
                    ),
                ),
            ),
        )

    def to_rm(rm: BitVector[3]) -> RoundingMode:
        return (rm==BV3(RM.RNE)).ite(
            RM_c(RM.RNE),
            (rm==BV3(RM.RTZ)).ite(
                RM_c(RM.RTZ),
                (rm == BV3(RM.RDN)).ite(
                    RM_c(RM.RDN),
                    (rm == BV3(RM.RUP)).ite(
                        RM_c(RM.RUP),
                        RM_c(RM.RMM),
                    ),
                ),
            ),
        )

    return SimpleNamespace(**locals())

@lru_cache(None)
def float_lib_gen(exp_bits: int, frac_bits: int):

    width = 1 + exp_bits + frac_bits
    Data = BitVector[width]

    #Returns a hwtypes float type
    @family_closure
    def Float_fc(family):
        if isinstance(family, MagmaFamily):
            Float = magma.BFloat[width]
            Float.reinterpret_from_bv = lambda bv: Float(bv)
            Float.reinterpret_as_bv = lambda f: magma.Bits[width](f)
            return Float
        elif isinstance(family, SMTFamily):
            return SMTFPVector[exp_bits, frac_bits, RM.RNE, False]
        else:
            return FPVector[exp_bits, frac_bits, RM.RNE, False]

    @family_closure
    def Abs_fc(family: TypeFamily):
        Float = Float_fc(family)

        @family.assemble(locals(), globals())
        class Abs(Peak, BlackBox):
            def __call__(self, in_: Data) -> Data:
                ...
        return Abs

    @family_closure
    def Neg_fc(family: TypeFamily):
        Float = Float_fc(family)

        @family.assemble(locals(), globals())
        class Neg(Peak, BlackBox):
            def __call__(self, in_: Data) -> Data:
                ...
        return Neg

    @family_closure
    def Add_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Add(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f + in1_f
                return Float.reinterpret_as_bv(res_f)
        return Add

    @family_closure
    def Sub_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Sub(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f - in1_f
                return Float.reinterpret_as_bv(res_f)
        return Sub

    @family_closure
    def Mul_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Mul(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f * in1_f
                return Float.reinterpret_as_bv(res_f)
        return Mul

    @family_closure
    def Div_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Div(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f / in1_f
                return Float.reinterpret_as_bv(res_f)
        return Div

    @family_closure
    def Fma_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Fma(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data, in2: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                in2_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f * in1_f + in2_f
                return Float.reinterpret_as_bv(res_f)
        return Fma

    @family_closure
    def Sqrt_fc(family: TypeFamily):
        Float = Float_fc(family)

        @family.assemble(locals(), globals())
        class Sqrt(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in_: Data) -> Data:
                ...
        return Sqrt


    @family_closure
    def RoundToIntegral_fc(family: TypeFamily):
        Float = Float_fc(family)

        @family.assemble(locals(), globals())
        class RoundToIntegral(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in_: Data) -> Data:
                ...
        return RoundToIntegral

    @family_closure
    def Add_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Add(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f + in1_f
                return Float.reinterpret_as_bv(res_f)
        return Add

    @family_closure
    def Sub_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Sub(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f - in1_f
                return Float.reinterpret_as_bv(res_f)
        return Sub

    @family_closure
    def Mul_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Mul(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f * in1_f
                return Float.reinterpret_as_bv(res_f)
        return Mul

    @family_closure
    def Div_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Div(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f / in1_f
                return Float.reinterpret_as_bv(res_f)
        return Div

    @family_closure
    def Fma_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Fma(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data, in2: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                in2_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f * in1_f + in2_f
                return Float.reinterpret_as_bv(res_f)
        return Fma

    @family_closure
    def Sqrt_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Sqrt(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in_: Data) -> Data:
                ...
        return Sqrt


    @family_closure
    def RoundToIntegral_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class RoundToIntegral(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in_: Data) -> Data:
                ...
        return RoundToIntegral

    @family_closure
    def Rem_fc(family: TypeFamily):
        Float = Float_fc(family)
        @family.assemble(locals(), globals())
        class Rem(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                in0_f = Float.reinterpret_from_bv(in0)
                in1_f = Float.reinterpret_from_bv(in1)
                res_f = in0_f % in1_f
                return Float.reinterpret_as_bv(res_f)
        return Rem


    @family_closure
    def Min_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Min(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Min

    @family_closure
    def Max_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Max(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Max

    @family_closure
    def Lte_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Lte(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Lte

    @family_closure
    def Lt_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Lt(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Lt

    @family_closure
    def Gte_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Gte(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Gte

    @family_closure
    def Gt_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Gt(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Gt

    @family_closure
    def Eq_fc(family: TypeFamily):
        @family.assemble(locals(), globals())
        class Eq(Peak, BlackBox):
            def __call__(self, in0: Data, in1: Data) -> Data:
                ...
        return Eq


    #Used to create floating point ops with a constant rounding mode
    @lru_cache(None)
    def const_rm(rm: RoundingMode):
        assert isinstance(rm, RoundingMode)
        @family_closure
        def _Add_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Add = Add_fc(family)
            @family.assemble(locals(), globals())
            class _Add(Peak):
                def __init__(self):
                    self.add: Add = Add()
                def __call__(self, in0: Data, in1: Data) -> Data:
                    return self.add(rm_, in0, in1)
            return _Add

        @family_closure
        def _Sub_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Sub = Sub_fc(family)
            @family.assemble(locals(), globals())
            class _Sub(Peak):
                def __init__(self):
                    self.sub: Sub = Sub()
                def __call__(self, in0: Data, in1: Data) -> Data:
                    return self.sub(rm_, in0, in1)
            return _Sub

        @family_closure
        def _Mul_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Mul = Mul_fc(family)
            @family.assemble(locals(), globals())
            class _Mul(Peak):
                def __init__(self):
                    self.mul: Mul = Mul()
                def __call__(self, in0: Data, in1: Data) -> Data:
                    return self.mul(rm_, in0, in1)
            return _Mul

        @family_closure
        def _Div_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Div = Div_fc(family)
            @family.assemble(locals(), globals())
            class _Div(Peak):
                def __init__(self):
                    self.div: Div = Div()
                def __call__(self, in0: Data, in1: Data) -> Data:
                    return self.div(rm_, in0, in1)
            return _Div

        @family_closure
        def _Fma_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Fma = Fma_fc(family)
            @family.assemble(locals(), globals())
            class _Fma(Peak):
                def __init__(self):
                    self.fma: Fma = Fma()
                def __call__(self, in0: Data, in1: Data, in2: Data) -> Data:
                    return self.fma(rm_, in0, in1, in2)
            return _Fma

        @family_closure
        def _Sqrt_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            Sqrt = Sqrt_fc(family)
            @family.assemble(locals(), globals())
            class _Sqrt(Peak):
                def __init__(self):
                    self.sqrt: Sqrt = Sqrt()
                def __call__(self, in_: Data) -> Data:
                    return self.sqrt(rm_, in_)
            return _Sqrt

        @family_closure
        def _RoundToIntegral_fc(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            RoundToIntegral = RoundToIntegral_fc(family)
            @family.assemble(locals(), globals())
            class _RoundToIntegral(Peak):
                def __init__(self):
                    self.r2i: RoundToIntegral = RoundToIntegral()
                def __call__(self, in_: Data) -> Data:
                    return self.r2i(rm_, in_)
            return _RoundToIntegral

        return SimpleNamespace(
            Add_fc=_Add_fc,
            Sub_fc=_Sub_fc,
            Mul_fc=_Mul_fc,
            Div_fc=_Div_fc,
            Sqrt_fc=_Sqrt_fc,
            Fma_fc=_Fma_fc,
            RoundToIntegral_fc=_RoundToIntegral_fc,
        )



    return SimpleNamespace(**locals())
