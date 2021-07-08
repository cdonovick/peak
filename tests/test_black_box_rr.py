import pytest

import examples.fp_pe as fp
from hwtypes import SMTBitVector as SBV, SMTBit as SBit

from examples.smallir import gen_SmallIR
from peak.family import SMTFamily, BlackBox
from peak.mapper import ArchMapper, RewriteRule
from peak.float import Float
from peak import Peak, family, family_closure, Const
from hwtypes import BitVector
from hwtypes.adt import Product, Enum


def test_float():
    fplib = Float(3, 4)
    add_obj = fplib.add_fc.Py()
    paths_to_bbs = BlackBox.get_black_boxes(add_obj)
    assert paths_to_bbs == {():add_obj}

def test_fp_pe_bb():
    PE = fp.PE_fc.Py
    pe = PE()
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for path in (
        ("FPU", "add"),
        ("FPU", "mul"),
        ("FPU", "sqrt"),
    ):
        assert path in paths_to_bbs
        bb_inst = paths_to_bbs[path]
        assert bb_inst is BlackBox.get_black_box(pe, path)
        assert isinstance(bb_inst, BlackBox)

def test_fp_pe_smt():
    pe = fp.PE_fc.SMT()
    AInst = SMTFamily().get_adt_t(fp.Inst)
    inst = AInst.from_fields(
        op=AInst.op(
            fpu=AInst.op.fpu(fp.FPU_op.FPAdd)
        ),
        imm=SBV[16](10),
        use_imm=SBit(name='ui')
    )
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for bb in paths_to_bbs.values():
        bb._set_outputs(SBV[16]())
    val = pe(inst, SBV[16](name='a'), SBV[16](2))
    for bb in paths_to_bbs.values():
        bb_inputs = bb._get_inputs()


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

    fplib = Float(3, 4)

    #Simple PE that can only add or not
    @family_closure
    def arch_fc(family):
        Data = BitVector[8]
        class Inst(Product):
            class Op(Enum):
                add = 1
                fpadd = 2

        Add = fplib.add_fc(family)
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
        (fplib.add_fc, True),
        (fplib.mul_fc, False),
    ):
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula=True)
        rewrite_rule = ir_mapper.solve('z3', external_loop=True)
        if found:
            assert rewrite_rule is not None
        else:
            assert rewrite_rule is None

ir = gen_SmallIR(16)
fplib = Float(7, 8)

@pytest.mark.parametrize('ir_fc, found', [
    (ir.instructions["Add"], True),
    (ir.instructions["Sub"], True),
    (ir.instructions["Mul"], False),
    (fplib.add_fc, True),
    (fplib.mul_fc, True),
    (fplib.sqrt_fc, True),
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
