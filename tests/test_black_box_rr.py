import pytest

import examples.fp_pe as fp

from examples.smallir import gen_SmallIR
from peak.mapper import ArchMapper, RewriteRule
from peak.float import float_lib_gen, RoudningMode_utils, RoundingMode
from peak import Peak, family, family_closure, Const
from hwtypes import BitVector
from hwtypes.adt import Product, Enum



def test_simple():
    print()

    @family_closure
    def ir_add_fc(family):
        Data = BitVector[8]

        @family.assemble(locals(), globals())
        class IR(Peak):
            def __call__(self, in0: Data, in1: Data) -> Data:
                return in0 + in1
        return IR

    fplib = float_lib_gen(3, 4)

    #Simple PE that can only add or not
    @family_closure
    def arch_fc(family):
        Data = BitVector[8]
        class Inst(Product):
            class Op(Enum):
                add = 1
                fpadd = 2

        Add = fplib.const_rm(RoundingMode.RNE).Add_fc(family)

        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __init__(self):
                self.fpadd: Add = Add()

            def __call__(self, inst: Const(Inst), a: Data, b: Data) -> Data:
                fpadd = self.fpadd(a, b)
                if inst.Op == Inst.Op.add:
                    return a + b
                else: #inst == Inst.OP.fpadd_
                    return fpadd
        return Arch

    arch_mapper = ArchMapper(arch_fc)
    for (ir_fc, found) in (
        (ir_add_fc, True),
        (fplib.const_rm(RoundingMode.RNE).Add_fc, True),
        (fplib.const_rm(RoundingMode.RNE).Mul_fc, False),
    ):
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula=True)
        rewrite_rule = ir_mapper.solve('z3', external_loop=True)
        if found:
            assert rewrite_rule is not None
            counter_example = rewrite_rule.verify()
            assert counter_example is None
        else:
            assert rewrite_rule is None

ir = gen_SmallIR(16)
fplib = float_lib_gen(7, 8).const_rm(RoundingMode.RDN)

@pytest.mark.parametrize('ir_fc, found', [
    (ir.instructions["Add"], True),
    (ir.instructions["Sub"], True),
    (ir.instructions["Mul"], False),
    (fplib.Add_fc, True),
    (fplib.Mul_fc, True),
    (fplib.Sqrt_fc, True),
])
def test_rr(ir_fc, found):
    arch_fc = fp.PE_fc
    arch_mapper = ArchMapper(arch_fc)

    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula=True)
    rewrite_rule = ir_mapper.solve('z3', external_loop=True)
    if not found:
        assert rewrite_rule is None
        return
    assert rewrite_rule is not None
    counter_example = rewrite_rule.verify()
    assert counter_example is None
