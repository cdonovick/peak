import pytest

from hwtypes import Bit, BitVector

from peak import family
from peak.mapper import ArchMapper, RewriteRule, read_serialized_bindings

from examples.smallir import gen_SmallIR
from examples.sum_pe.sim import PE_fc as PE_fc_s
from examples.tagged_pe.sim import PE_fc as PE_fc_t

@pytest.mark.parametrize('arch_fc', [PE_fc_s, PE_fc_t])
def test_rr_serialization(arch_fc):
    IR = gen_SmallIR(8)
    arch_mapper = ArchMapper(arch_fc)
    expect_found = ('Add', 'Sub', 'And', 'Nand', 'Or', 'Nor')
    expect_not_found = ('Mul', 'Shftr', 'Shftl', 'Not', 'Neg')
    for ir_name, ir_fc in IR.instructions.items():
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
        rewrite_rule = ir_mapper.solve('z3', external_loop=True)
        if rewrite_rule is None:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found
        serialized_bindings = rewrite_rule.serialize_bindings()
        new_rewrite_rule = read_serialized_bindings(serialized_bindings, ir_fc, arch_fc)
        assert rewrite_rule.ibinding == new_rewrite_rule.ibinding
        assert rewrite_rule.obinding == new_rewrite_rule.obinding

