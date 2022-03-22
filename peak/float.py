import inspect

from functools import lru_cache
from types import SimpleNamespace

from peak import family_closure, Peak
from peak.family import SMTFamily, MagmaFamily
from hwtypes import SMTFPVector, FPVector, RoundingMode as RoundingMode_hwtypes, TypeFamily
from hwtypes.fp_vector_abc import AbstractFPVector
from peak.black_box import BlackBox
from hwtypes import BitVector, Bit
from hwtypes.adt import Enum
import magma

class RoundingMode(Enum):
    RNE = 0
    RTZ = 1
    RDN = 2 #RTN
    RUP = 3 #RTP
    RMM = 4 #RNA

def RoudningMode_utils(family):
    RM = RoundingMode
    RM_c = family.get_constructor(RoundingMode)
    BV3 = lambda e: family.BitVector[3](e.value)
    def RM_to_RM_hwtypes(rm: RoundingMode) -> RoundingMode_hwtypes:
        return {
            RoundingMode.RNE: RoundingMode_hwtypes.RNE,
            RoundingMode.RTZ: RoundingMode_hwtypes.RTZ,
            RoundingMode.RDN: RoundingMode_hwtypes.RTN,
            RoundingMode.RUP: RoundingMode_hwtypes.RTP,
            RoundingMode.RMM: RoundingMode_hwtypes.RNA,
        }[rm]
    def RM_hwtypes_to_RM(rm: RoundingMode_hwtypes) -> RoundingMode:
        return {
            RoundingMode_hwtypes.RNE: RoundingMode.RNE,
            RoundingMode_hwtypes.RTZ: RoundingMode.RTZ,
            RoundingMode_hwtypes.RTN: RoundingMode.RDN,
            RoundingMode_hwtypes.RTP: RoundingMode.RUP,
            RoundingMode_hwtypes.RNA: RoundingMode.RMM,
        }[rm]

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


def _format_name(name: str) -> str:
    assert name[:3] == 'fp_', name
    return name[3:].capitalize() + '_fc'

@lru_cache(None)
def float_lib_gen(exp_bits: int, frac_bits: int, ieee_compliance: bool = False):

    width = 1 + exp_bits + frac_bits
    Data = BitVector[width]

    def _cast_magma(rm, x):
        if rm is not RoundingMode_hwtypes.RNE:
            raise NotImplementedError("Only supports RNE")
        Float = magma.BFloat[width]
        Float.reinterpret_from_bv = lambda bv: Float(bv)
        Float.reinterpret_as_bv = lambda f: magma.Bits[width](f)
        Float.fp_add = lambda x, y: x + y
        Float.fp_mul = lambda x, y: x * y
        return Float.reinterpret_from_bv(x)

    def _cast_smt(rm, x):
        if not isinstance(rm, RoundingMode_hwtypes):
            raise ValueError("Rounding Mode need to be hwtypes version")
        return SMTFPVector[exp_bits, frac_bits, rm, ieee_compliance].reinterpret_from_bv(x)

    def _cast_py(rm, x):
        if not isinstance(rm, RoundingMode_hwtypes):
            raise ValueError("Rounding Mode need to be hwtypes version")
        return FPVector[exp_bits, frac_bits, rm, ieee_compliance].reinterpret_from_bv(x)

    def _get_cast(family):
        if isinstance(family, MagmaFamily):
            return _cast_magma
        elif isinstance(family, SMTFamily):
            return _cast_smt
        else:
            return _cast_py

    def _get_cast_const_rm(rm: RoundingMode, family):
        rm_hwtypes = RoudningMode_utils(family).RM_to_RM_hwtypes(rm)
        cast = _get_cast(family)
        return lambda x: cast(rm_hwtypes, x)


    @lru_cache(None)
    def gen_binary(op_name):
        @family_closure
        def fc(family: TypeFamily):
            cast = _get_cast(family)
            @family.assemble(locals(), globals())
            class Op(Peak, BlackBox):
                def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Data:
                    if rm == RoundingMode.RNE:
                        in0_rne = cast(RoundingMode_hwtypes.RNE, in0)
                        in1_rne = cast(RoundingMode_hwtypes.RNE, in1)
                        out_rne = getattr(in0_rne, op_name)(in1_rne)
                        out = out_rne.reinterpret_as_bv()
                    elif rm == RoundingMode.RTZ:
                        in0_rtz = cast(RoundingMode_hwtypes.RTZ, in0)
                        in1_rtz = cast(RoundingMode_hwtypes.RTZ, in1)
                        out_rtz = getattr(in0_rtz, op_name)(in1_rtz)
                        out = out_rtz.reinterpret_as_bv()
                    elif rm == RoundingMode.RDN:
                        in0_rdn = cast(RoundingMode_hwtypes.RDN, in0)
                        in1_rdn = cast(RoundingMode_hwtypes.RDN, in1)
                        out_rdn = getattr(in0_rdn, op_name)(in1_rdn)
                        out = out_rdn.reinterpret_as_bv()
                    elif rm == RoundingMode.RUP:
                        in0_rup = cast(RoundingMode_hwtypes.RUP, in0)
                        in1_rup = cast(RoundingMode_hwtypes.RUP, in1)
                        out_rup = getattr(in0_rup, op_name)(in1_rup)
                        out = out_rup.reinterpret_as_bv()
                    else:
                        assert  rm == RoundingMode.RMM
                        in0_rmm = cast(RoundingMode_hwtypes.RUP, in0)
                        in1_rmm = cast(RoundingMode_hwtypes.RUP, in1)
                        out_rmm = getattr(in0_rmm, op_name)(in1_rmm)
                        out = out_rmm.reinterpret_as_bv()
                    return out
            return Op
        return fc

    @lru_cache(None)
    def gen_binary_bit(op_name):
        @family_closure
        def fc(family: TypeFamily):
            cast = _get_cast(family)
            @family.assemble(locals(), globals())
            class Op(Peak, BlackBox):
                def __call__(self, rm: RoundingMode, in0: Data, in1: Data) -> Bit:
                    if rm == RoundingMode.RNE:
                        in0_rne = cast(RoundingMode_hwtypes.RNE, in0)
                        in1_rne = cast(RoundingMode_hwtypes.RNE, in1)
                        out_rne = getattr(in0_rne, op_name)(in1_rne)
                        out = out_rne
                    elif rm == RoundingMode.RTZ:
                        in0_rtz = cast(RoundingMode_hwtypes.RTZ, in0)
                        in1_rtz = cast(RoundingMode_hwtypes.RTZ, in1)
                        out_rtz = getattr(in0_rtz, op_name)(in1_rtz)
                        out = out_rtz
                    elif rm == RoundingMode.RDN:
                        in0_rdn = cast(RoundingMode_hwtypes.RDN, in0)
                        in1_rdn = cast(RoundingMode_hwtypes.RDN, in1)
                        out_rdn = getattr(in0_rdn, op_name)(in1_rdn)
                        out = out_rdn
                    elif rm == RoundingMode.RUP:
                        in0_rup = cast(RoundingMode_hwtypes.RUP, in0)
                        in1_rup = cast(RoundingMode_hwtypes.RUP, in1)
                        out_rup = getattr(in0_rup, op_name)(in1_rup)
                        out = out_rup
                    else:
                        assert  rm == RoundingMode.RMM
                        in0_rmm = cast(RoundingMode_hwtypes.RUP, in0)
                        in1_rmm = cast(RoundingMode_hwtypes.RUP, in1)
                        out_rmm = getattr(in0_rmm, op_name)(in1_rmm)
                        out = out_rmm
                    return out
            return Op
        return fc

    @lru_cache(None)
    def gen_unary(op_name):
        @family_closure
        def fc(family: TypeFamily):
            cast = _get_cast(family)
            @family.assemble(locals(), globals())
            class Op(Peak, BlackBox):
                def __call__(self, rm: RoundingMode, in0: Data) -> Data:
                    if rm == RoundingMode.RNE:
                        in0_rne = cast(RoundingMode_hwtypes.RNE, in0)
                        out_rne = getattr(in0_rne, op_name)()
                        out = out_rne.reinterpret_as_bv()
                    elif rm == RoundingMode.RTZ:
                        in0_rtz = cast(RoundingMode_hwtypes.RTZ, in0)
                        out_rtz = getattr(in0_rtz, op_name)()
                        out = out_rtz.reinterpret_as_bv()
                    elif rm == RoundingMode.RDN:
                        in0_rdn = cast(RoundingMode_hwtypes.RDN, in0)
                        out_rdn = getattr(in0_rdn, op_name)()
                        out = out_rdn.reinterpret_as_bv()
                    elif rm == RoundingMode.RUP:
                        in0_rup = cast(RoundingMode_hwtypes.RUP, in0)
                        out_rup = getattr(in0_rup, op_name)()
                        out = out_rup.reinterpret_as_bv()
                    else:
                        assert  rm == RoundingMode.RMM
                        in0_rmm = cast(RoundingMode_hwtypes.RUP, in0)
                        out_rmm = getattr(in0_rmm, op_name)()
                        out = out_rmm.reinterpret_as_bv()
                    return out
            return Op
        return fc

    closures = {}
    for k, f in AbstractFPVector.__dict__.items():
        if k.startswith('fp_'):
            if len(inspect.signature(f).parameters) == 1:
                closures[_format_name(k)] = gen_unary(k)
            elif k in ("fp_leq", "fp_lt", "fp_geq", "fp_gt", "fp_eq"):
                closures[_format_name(k)] = gen_binary_bit(k)
            elif len(inspect.signature(f).parameters) == 2:
                closures[_format_name(k)] = gen_binary(k)

    @family_closure
    def fp_fma(family):
        cast = _get_cast(family)
        @family.assemble(locals(), globals())
        class FMA(Peak, BlackBox):
            def __call__(self, rm: RoundingMode, in0: Data, in1: Data, in2: Data) -> Data:
                if rm == RoundingMode.RNE:
                    in0_rne = cast(RoundingMode_hwtypes.RNE, in0)
                    in1_rne = cast(RoundingMode_hwtypes.RNE, in1)
                    in2_rne = cast(RoundingMode_hwtypes.RNE, in2)
                    out_rne = in0_rne.fp_fma(in1_rne, in2_rne)
                    out = out_rne.reinterpret_as_bv()
                elif rm == RoundingMode.RTZ:
                    in0_rtz = cast(RoundingMode_hwtypes.RTZ, in0)
                    in1_rtz = cast(RoundingMode_hwtypes.RTZ, in1)
                    in2_rtz = cast(RoundingMode_hwtypes.RTZ, in2)
                    out_rtz = in0_rtz.fp_fma(in1_rtz, in2_rtz)
                    out = out_rtz.reinterpret_as_bv()
                elif rm == RoundingMode.RDN:
                    in0_rdn = cast(RoundingMode_hwtypes.RDN, in0)
                    in1_rdn = cast(RoundingMode_hwtypes.RDN, in1)
                    in2_rdn = cast(RoundingMode_hwtypes.RDN, in2)
                    out_rdn = in0_rdn.fp_fma(in1_rdn, in2_rdn)
                    out = out_rdn.reinterpret_as_bv()
                elif rm == RoundingMode.RUP:
                    in0_rup = cast(RoundingMode_hwtypes.RUP, in0)
                    in1_rup = cast(RoundingMode_hwtypes.RUP, in1)
                    in2_rup = cast(RoundingMode_hwtypes.RUP, in2)
                    out_rup = in0_rup.fp_fma(in1_rup, in2_rup)
                    out = out_rup.reinterpret_as_bv()
                else:
                    assert  rm == RoundingMode.RMM
                    in0_rmm = cast(RoundingMode_hwtypes.RUP, in0)
                    in1_rmm = cast(RoundingMode_hwtypes.RUP, in1)
                    in2_rmm = cast(RoundingMode_hwtypes.RUP, in2)
                    out_rmm = in0_rmm.fp_fma(in1_rmm, in2_rmm)
                    out = out_rmm.reinterpret_as_bv()
                return out
        return FMA


    closures[_format_name('fp_fma')] = fp_fma


    #Used to create floating point ops with a constant rounding mode


    @lru_cache(None)
    def const_rm(rm: RoundingMode):
        assert isinstance(rm, RoundingMode)

        def gen_const_rm_unary(op_name):
            @family_closure
            def fc(family):
                cast = _get_cast_const_rm(rm, family)

                @family.assemble(locals(), globals())
                class Op(Peak, BlackBox):
                    def __call__(self, in_: Data) -> Data:
                        in_float = cast(in_)
                        out_float = getattr(in_float, op_name)()
                        out = out_float.reinterpret_as_bv()
                        return out

                return Op

            return fc

        def gen_const_rm_binary(op_name):
            @family_closure
            def fc(family):
                cast = _get_cast_const_rm(rm, family)

                @family.assemble(locals(), globals())
                class Op(Peak, BlackBox):
                    def __call__(self, in0: Data, in1: Data) -> Data:
                        in0_float = cast(in0)
                        in1_float = cast(in1)
                        out_float = getattr(in0_float, op_name)(in1_float)
                        out = out_float.reinterpret_as_bv()
                        return out

                return Op

            return fc

        def gen_const_rm_binary_bit(op_name):
            @family_closure
            def fc(family):
                cast = _get_cast_const_rm(rm, family)

                @family.assemble(locals(), globals())
                class Op(Peak, BlackBox):
                    def __call__(self, in0: Data, in1: Data) -> Bit:
                        in0_float = cast(in0)
                        in1_float = cast(in1)
                        out_bit = getattr(in0_float, op_name)(in1_float)
                        return out_bit

                return Op

            return fc

        closures_ = {}
        for k, f in AbstractFPVector.__dict__.items():
            if k.startswith('fp_'):
                if len(inspect.signature(f).parameters) == 1:
                    closures_[_format_name(k)] = gen_const_rm_unary(k)
                elif k in ("fp_leq", "fp_lt", "fp_geq", "fp_gt", "fp_eq"):
                    closures_[_format_name(k)] = gen_const_rm_binary_bit(k)
                elif len(inspect.signature(f).parameters) == 2:
                    closures_[_format_name(k)] = gen_const_rm_binary(k)

        @family_closure
        def _fp_fma(family):
            rm_ = family.get_constructor(RoundingMode)(rm)
            FMA = fp_fma_fc(family)
            @family.assemble(locals(), globals())
            class _FMA(Peak):
                def __init__(self):
                    self.fma : FMA = FMA()

                def __call__(self, in0: Data, in1: Data, in2: Data) -> Data:
                    return self.fma(rm_, in0, in1, in2)
            return _FMA

        closures_[_format_name('fp_fma')] = _fp_fma
        return SimpleNamespace(**closures_)


    closures['const_rm'] = const_rm
    return SimpleNamespace(**closures)
