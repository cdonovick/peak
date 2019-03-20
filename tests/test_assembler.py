from peak.adt import Product, Sum
from peak.auto_assembler import generate_assembler
from peak.demo_pes.pe5.isa import INST as pe5_isa
from peak.arm.isa import Inst as arm_isa
from peak.pico.isa import Inst as pico_isa
from hwtypes import BitVector

import pytest

@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa])
def test_assembler_disassembler(isa):
    assembler, disassembler, width, layout =  generate_assembler(isa)
    for inst in isa.enumerate():
        opcode = assembler(inst)
        assert isinstance(opcode, BitVector[width])
        assert disassembler(opcode) == inst

        if isinstance(isa, Product):
            for name,field in isa._fields_dict.items():
                e,d,w,l = generate_assembler(field)
                assert l == layout[name][2]
                sub_opcode = opcode[layout[name][0] : layout[name][1]]
                assert sub_opcode.size <= w
                assert isinstance(d(sub_opcode), field)
        elif isinstance(isa, Sum):
            for field in isa.fields:
                e,d,w,l = generate_assembler(field)
                assert l == layout[field][2]
                sub_opcode = opcode[layout[field][0] : layout[field][1]]
                assert sub_opcode.size <= w
                assert isinstance(d(sub_opcode), field)

    if isinstance(isa, Product):
        for name,field in isa._fields_dict.items():
            e,d,w,l = generate_assembler(field)
            for inst in field.enumerate():
                opcode = e(inst)
                assert isinstance(opcode, BitVector[w])
                assert d(opcode) == inst
    elif isinstance(isa, Sum):
        for field in isa.fields:
            e,d,w,l = generate_assembler(field)
            for inst in field.enumerate():
                opcode = e(inst)
                assert isinstance(opcode, BitVector[w])
                assert d(opcode) == inst

