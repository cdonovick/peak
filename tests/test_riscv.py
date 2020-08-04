import itertools
import random

import pytest

from examples.riscv import sim as sim_mod_base
from examples.riscv import isa as isa_mod_base
from examples.riscv import family as family_base
from examples.riscv_ext import sim as sim_mod_ext, isa as isa_mod_ext
from examples.riscv import asm
from peak.mapper.utils import rebind_type


NTESTS = 16

GOLD = {
        'ADD': lambda a, b: a + b,
        'SUB': lambda a, b: a - b,
        'SLT': lambda a, b: type(a)(a.bvslt(b)),
        'SLTU': lambda a, b: type(a)(a.bvult(b)),
        'AND': lambda a, b: a & b,
        'OR': lambda a, b: a | b,
        'XOR': lambda a, b: a ^ b,
        'SLL': lambda a, b: a.bvshl(b),
        'SRL': lambda a, b: a.bvlshr(b),
        'SRA': lambda a, b: a.bvashr(b),
}



@pytest.mark.parametrize('fcs', [(sim_mod_base, isa_mod_base),
                                 (sim_mod_ext, isa_mod_ext)])
@pytest.mark.parametrize('op_name',
        ('ADD', 'SUB', 'SLT', 'SLTU', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA',)
    )
@pytest.mark.parametrize('use_imm', (False, True))
def test_riscv(fcs, op_name, use_imm):
    R32I = fcs[0].R32I_fc.Py
    isa = fcs[1].ISA_fc.Py
    riscv = R32I()
    for i in range(1, 32):
        riscv.register_file.store(isa.Idx(i), isa.Word(i))

    asm_f = getattr(asm, f'asm_{op_name}')
    for _ in range(NTESTS):
        rs1 = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
        rd = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
        if use_imm:
            imm = random.randrange(0, 1 << 5)
            inst = asm_f(rs1=rs1, imm=imm, rd=rd)
            a = riscv.register_file.load1(rs1)
            b = isa.Word(imm)
        else:
            rs2 = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
            inst = asm_f(rs1=rs1, rs2=rs2, rd=rd)
            a = riscv.register_file.load1(rs1)
            b = riscv.register_file.load1(rs2)

        pc = isa.Word(random.randrange(0, 1 << isa.Word.size, 4))
        pc_next = riscv(inst, pc)
        assert pc_next == pc + 4
        assert GOLD[op_name](a, b) == riscv.register_file.load1(rd)


def test_riscv_smt():
    fam = family_base.SMTFamily()
    R32I = sim_mod_base.R32I_mappable_fc(fam)
    isa = isa_mod_base.ISA_fc.Py

    AsmInst = fam.get_adt_t(isa.Inst)

    riscv = R32I()

    rs1_v = fam.Word(name='rs1')
    rs2_v = fam.Word(name='rs2')
    rd_init = fam.Word(name='rd_init')
    pc = fam.Word(name='pc')


    r0 = isa.Idx(0)
    rs1 = isa.Idx(1)
    rs2 = isa.Idx(2)
    rd  = isa.Idx(3)

    data  = isa.R(rd=rd, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(arith=isa.ArithInst.SUB)
    op = isa.OP(data=data, tag=tag)
    inst = isa.Inst(op)

    asm_inst = AsmInst(inst)

    pc_next, rd_next = riscv(asm_inst, pc, rs1_v, rs2_v, rd_init)

    # Recall pysmt == is structural equiv
    assert pc_next.value == (pc.value + 4)
    assert rd_next.value == (rs1_v.value - rs2_v.value)
    assert rd_next.value == (rs1_v - rs2_v).value
    assert rd_next.value != rd_init.value


    # setting rd=r0 makes this a nop
    data  = isa.R(rd=r0, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(arith=isa.ArithInst.SUB)
    op = isa.OP(data=data, tag=tag)
    inst = isa.Inst(op)

    asm_inst = AsmInst(inst)

    pc_next, rd_next = riscv(asm_inst, pc, rs1_v, rs2_v, rd_init)

    assert pc_next.value == (pc.value + 4)
    assert rd_next.value != (rs1_v.value - rs2_v.value)
    assert rd_next.value != (rs1_v - rs2_v).value
    assert rd_next.value == rd_init.value


@pytest.mark.parametrize('op_name',
        ('ADD', 'SUB', 'SLT', 'SLTU', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA',)
    )
@pytest.mark.parametrize('use_imm', (False, True))
def test_get_set_fields(op_name, use_imm):
    # SUBI doesn't techinicaly exist
    if op_name == 'SUB' and use_imm:
        return

    isa = isa_mod_base.ISA_fc.Py
    asm_f = getattr(asm, f'asm_{op_name}')

    # because I need a do while loop
    inst1 = 0
    inst2 = 0
    KWARG_SCHEMA = {
        'rs1': None,
        'rs2': None,
        'rd': None,
        'imm': None,
    }


    while inst1 == inst2:
        kwargs1 = KWARG_SCHEMA.copy()
        kwargs2 = KWARG_SCHEMA.copy()
        for d in (kwargs1, kwargs2):
            for key in KWARG_SCHEMA:
                if use_imm and key == 'rs2':
                    continue
                elif not use_imm and key == 'imm':
                    continue
                d[key] = random.randrange(0, 1 << isa.Idx.size)

        inst1 = asm_f(**kwargs1)
        inst2 = asm_f(**kwargs2)
        assert  (inst1 == inst2) == (kwargs1 == kwargs2)
        assert asm.get_fields(inst1) == kwargs1
        assert asm.get_fields(inst2) == kwargs2

    assert inst1 != inst2
    assert asm.set_fields(inst1, **kwargs2) == inst2
    assert asm.set_fields(inst2, **kwargs1) == inst1

def test_rebind():
    isa = isa_mod_base.ISA_fc.Py
    Inst_py = isa.Inst
    Inst_smt = rebind_type(Inst_py, family_base.SMTFamily())


