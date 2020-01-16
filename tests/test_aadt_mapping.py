from hwtypes import Bit, BitVector
from hwtypes.adt import Enum, Product

from peak.mapper.utils import pretty_print_binding
from peak.mapper import ArchMapper
from peak import Const, family_closure, Peak, name_outputs, update_peak
from examples.min_pe.sim import PE_fc
from examples.smallir import gen_SmallIR

num_test_vectors = 16
def test_automapper():
    IR = gen_SmallIR(8)
    arch_fc = PE_fc
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


#This will test the const modifier
def test_const():

    #Testing out something like coreir const
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, const_value : Const(Data)):
                return const_value
        return update_peak(IR, family)

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        class Op(Enum):
            add = 1
            const = 2
        class Inst(Product):
            op = Op
            imm = Data

        class Arch(Peak):
            @name_outputs(out=Data)
            def __call__(self, inst : Const(Inst), in0 : Data, in1 : Data):
                if inst.op == Op.add:
                    return in0 + in1
                else: #inst.op == Op.const
                    return inst.imm
        return update_peak(Arch, family)

    arch_fc = Arch_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    solution = ir_mapper.solve('z3')
    assert solution.solved
    assert (('const_value',), ('inst', 'imm')) in solution.ibinding
