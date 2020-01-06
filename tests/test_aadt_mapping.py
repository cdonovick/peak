from hwtypes import Bit, BitVector
from peak.mapper.utils import pretty_print_binding
from peak.mapper import ArchMapper
from examples.min_pe.sim import gen_sim
from examples.smallir import gen_SmallIR

num_test_vectors = 16
def test_min_pe_auto():
    IR = gen_SmallIR(8)
    arch_fc = lambda f: gen_sim(f)[3]
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    expect_found = ('Add', 'Sub', 'And', 'Nand', 'Or', 'Nor', 'Not', 'Neg')
    expect_not_found = ('Mul', 'Shftr', 'Shftl')
    for ir_name, ir_fc in IR.instructions.items():
        print(ir_name)
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
        solution = ir_mapper.solve('z3')
        if not solution.solved:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found
        pretty_print_binding(solution.ibinding)

        #verify the mapping works
        ir_bv = ir_fc(Bit.get_family())
        for _ in range(num_test_vectors):
            ir_vals = {path:BitVector.random(8) for path in solution.ir_bounded}
            ir_inputs = solution.build_ir_input(ir_vals)
            arch_inputs = solution.build_arch_input(ir_vals)
            assert ir_bv()(**ir_inputs) == arch_bv()(**arch_inputs)

test_min_pe_auto()
