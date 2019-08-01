from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
from hwtypes import BitVector
from hwtypes import make_modifier
from hwtypes.adt import Product, Tuple, Sum
import pytest

FooBV = make_modifier('Foo')(BitVector)
BarBV = make_modifier('Bar')(BitVector)


@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa])
@pytest.mark.parametrize("bv_type", [BarBV, FooBV])
def test_assembled_adt(isa, bv_type):
    def _check_recursive(isa, bv_type):
        asm_adt = AssembledADT[isa, Assembler, bv_type]
        asm = Assembler(isa)

        for inst in isa.enumerate():
            opcode = asm.assemble(inst, bv_type=bv_type)
            assert asm_adt(inst) == asm_adt(opcode)
            assert issubclass(type(asm_adt(inst)._value_), bv_type)
            assert issubclass(type(asm_adt(opcode)._value_), bv_type)

            assert asm_adt(inst) == inst
            assert asm_adt(inst) == opcode

            assert asm_adt(opcode) == inst
            assert asm_adt(opcode) == opcode


        for name,field in isa.field_dict.items():
            assert getattr(asm_adt, name) is AssembledADT[field, Assembler, bv_type]
            if isinstance(field, (Product, Tuple, Sum)):
                _check_recursive(field, bv_type)

    _check_recursive(isa, bv_type)
