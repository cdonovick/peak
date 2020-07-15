import itertools
import random

import pytest

from examples.riscv import sim as sim_mod, isa as isa_mod, family
from examples.riscv import asm


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


@pytest.mark.parametrize('op_name',
        ('ADD', 'SUB', 'SLT', 'SLTU', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA',)
    )
@pytest.mark.parametrize('use_imm', (False, True))
def test_riscv(op_name, use_imm):
    R32I = sim_mod.R32I_fc.Py
    isa = isa_mod.ISA_fc.Py
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
    fam = family.SMTFamily()
    R32I = sim_mod.R32I_mappable_fc(fam)
    isa = isa_mod.ISA_fc.Py

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
def test_set_fields(op_name, use_imm):
    # SUBI doesn't techinicaly exist
    if op_name == 'SUB' and use_imm:
        return

    isa = isa_mod.ISA_fc.Py
    asm_f = getattr(asm, f'asm_{op_name}')

    # because I need a do while loop
    inst1 = 0
    inst2 = 0
    while inst1 == inst2:
        rs1  = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
        rs1_ = isa.Idx(random.randrange(1, 1 << isa.Idx.size))

        rd  = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
        rd_ = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
        if use_imm:
            imm  = random.randrange(0, 1 << 5)
            imm_ = random.randrange(0, 1 << 5)
            rs2  = None
            rs2_ = None
        else:
            imm  = None
            imm_ = None
            rs2  = isa.Idx(random.randrange(1, 1 << isa.Idx.size))
            rs2_ = isa.Idx(random.randrange(1, 1 << isa.Idx.size))

        inst1 = asm_f(rs1=rs1,  rs2=rs2,  imm=imm,  rd=rd)
        inst2 = asm_f(rs1=rs1_, rs2=rs2_, imm=imm_, rd=rd_)
        assert ((rs1 == rs1_ and  rs2 == rs2_ and imm == imm_ and rd == rd_)
                or inst1 != inst2)

    assert inst1 != inst2

    assert asm.set_fields(inst1, rs1=rs1_, rs2=rs2_, imm=imm_, rd=rd_) == inst2
    assert asm.set_fields(inst2, rs1=rs1,  rs2=rs2,  imm=imm,  rd=rd)  == inst1
