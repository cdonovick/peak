import pytest

from hwtypes import AbstractBitVector
from hwtypes.adt import Enum, Product, Tuple, Sum
from hwtypes.adt import new_instruction
from hwtypes import BitVector
from hwtypes import new

from peak.assembler.assembler import Assembler
from peak.assembler2.assembler import Assembler as Assembler2

from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
from examples.min_pe.isa import ISA_fc as gen_min_isa


FooBV = new(BitVector, name='FooBV')
BarBV = new(BitVector, name='BarBV')

_, _, min_isa = gen_min_isa(BitVector.get_family())
assert issubclass(min_isa, Product)

@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa, min_isa])
@pytest.mark.parametrize("bv_type", [BarBV, FooBV])
def test_assembler_disassembler(isa, bv_type):
    assembler = Assembler(isa)
    for inst in isa.enumerate():
        opcode = assembler.assemble(inst, bv_type=bv_type)
        assert isinstance(opcode, bv_type[assembler.width])
        assert assembler.is_valid(opcode)
        assert assembler.disassemble(opcode) == inst

        for name, field in isa.field_dict.items():
            sub_assembler = Assembler(field)
            if issubclass(isa, Sum):
                assert assembler.sub[field].asm is sub_assembler
            if issubclass(isa, Tuple):
                assert assembler.sub[name].asm is sub_assembler
            if issubclass(isa, Product):
                assert getattr(assembler.sub, name).asm is sub_assembler

            if issubclass(isa, Tuple):
                sub_opcode = opcode[assembler.sub[name].idx]
                assert isinstance(sub_opcode, bv_type[sub_assembler.width])
                assert sub_assembler.is_valid(sub_opcode)
                sub_inst = sub_assembler.disassemble(sub_opcode)
                assert isinstance(sub_inst, field)
                assert sub_inst == inst.value_dict[name]
            elif issubclass(isa, Sum) and inst[field].match:
                sub_opcode = opcode[assembler.sub[field].idx]
                assert isinstance(sub_opcode, bv_type[sub_assembler.width])
                assert sub_assembler.is_valid(sub_opcode)
                sub_inst = sub_assembler.disassemble(sub_opcode)
                assert isinstance(sub_inst, field)
                assert sub_inst == inst.value_dict[name]


@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa, min_isa])
@pytest.mark.parametrize("bv_type", [BarBV, FooBV])
def test_assembler_disassembler_v2(isa, bv_type):
    def _check_recursive(isa, bv_type):
        assembler = Assembler2(isa)
        for inst in isa.enumerate():
            opcode = assembler.assemble(inst, bv_type=bv_type)
            assert isinstance(opcode, bv_type[assembler.width])
            assert assembler.is_valid(opcode)
            assert assembler.disassemble(opcode) == inst

            for name, field in isa.field_dict.items():
                if issubclass(isa, Sum) and not inst[field].match:
                    continue

                sub_assembler = Assembler(field)
                sub_opcode = sub_assembler.assemble(inst.value_dict[name])
                sub_opcode_ = assembler.extract(opcode, name)
                assert sub_opcode == sub_opcode_
                sub_inst = sub_assembler.disassemble(sub_opcode)
                sub_inst_ = sub_assembler.disassemble(sub_opcode_)
                assert sub_inst_ == sub_inst
                assert sub_inst_ == sub_inst
                assert sub_inst == inst.value_dict[name]

                if isinstance(field, (Sum, Tuple, Product)):
                    _check_recursive(field, bv_type)

    _check_recursive(isa, bv_type)


@pytest.mark.parametrize("asm_t", [Assembler, Assembler2])
def test_enum_determinism(asm_t):
    def assemble():
        class ALUOP(Enum):
            Add = new_instruction()
            Sub = new_instruction()
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()

        assembler = asm_t(ALUOP)
        instr_bv = assembler.assemble(ALUOP.Or)
        return int(instr_bv)
    val = assemble()
    for _ in range(100):
        assert val == assemble()


@pytest.mark.parametrize("asm_t", [Assembler, Assembler2])
def test_product_determinism(asm_t):
    def assemble():
        class ALUOP(Enum):
            Add = new_instruction()
            Sub = new_instruction()
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()

        class Inst(Product):
            alu_op1 = ALUOP
            alu_op2 = ALUOP

        assembler = asm_t(Inst)
        instr_bv = assembler.assemble(Inst(ALUOP.Add, ALUOP.Sub))
        return int(instr_bv)
    val = assemble()
    for _ in range(100):
        assert val == assemble()


@pytest.mark.parametrize("asm_t", [Assembler, Assembler2])
def test_sum_determinism(asm_t):
    def assemble():
        class OP1(Enum):
            Add = new_instruction()
            Sub = new_instruction()

        class OP2(Enum):
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()


        class Inst(Sum[OP1, OP2]): pass

        assembler = asm_t(Inst)
        add_instr = Inst(OP1.Add)
        instr_bv = assembler.assemble(add_instr)
        return int(instr_bv)

    val = assemble()
    for _ in range(100):
        assert val == assemble()
