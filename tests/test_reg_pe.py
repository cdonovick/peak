import pytest
import random

from examples.reg_file import sim as sim_mod, isa as isa_mod
family = sim_mod.family

isa = isa_mod.ISA_fc.Py

NTESTS = 32

GOLDS = {
    isa.BOp.Add: lambda a, b: a + b,
    isa.BOp.Nor: lambda a, b: ~(a | b),
    isa.UOp.Inv: lambda a, b: ~a,
    isa.UOp.Mov: lambda a, b: a,
}

ASM = {
    isa.BOp.Add: lambda rs1, rs2, rd: isa.Inst(b=isa.BLayout(isa.BOp.Add, rs1, rs2, rd)),
    isa.BOp.Nor: lambda rs1, rs2, rd: isa.Inst(b=isa.BLayout(isa.BOp.Nor, rs1, rs2, rd)),
    isa.UOp.Inv: lambda rs1, rs2, rd: isa.Inst(u=isa.ULayout(isa.UOp.Inv, rs1, rd)),
    isa.UOp.Mov: lambda rs1, rs2, rd: isa.Inst(u=isa.ULayout(isa.UOp.Mov, rs1, rd)),
}

OP = random.choices(list(ASM.keys()), k=NTESTS)
RS1 = tuple(map(isa.Idx, random.choices(range(1, 32), k=NTESTS)))
RS2 = tuple(map(isa.Idx, random.choices(range(1, 32), k=NTESTS)))
RD =  tuple(map(isa.Idx, random.choices(range(1, 32), k=NTESTS)))

def test_py():
    PyPE = sim_mod.RegPE_fc.Py

    pe = PyPE()
    for i in range(1, 1 << isa.Idx.size):
        pe.register_file.store(isa.Idx(i), isa.Word(i))

    for op, rs1, rs2, rd in zip(OP, RS1, RS2, RD):
        a = pe.register_file.load1(rs1)
        b = pe.register_file.load2(rs2)
        inst = ASM[op](rs1, rs2, rd)
        pe(inst)
        assert pe.register_file.load1(rd) == GOLDS[op](a, b)


def test_smt():
    fam = family.SMTFamily()
    SMTPe = sim_mod.RegPE_mappable_fc.SMT
    isa = isa_mod.ISA_fc.Py

    pe = SMTPe()

    rs1_v = fam.Word(name='rs1')
    rs2_v = fam.Word(name='rs2')
    rd_init = fam.Word(name='rd_init')

    RS1 = map(isa.Idx, random.choices(range(1, 32), k=NTESTS))
    RS2 = map(isa.Idx, random.choices(range(1, 32), k=NTESTS))
    RD = map(isa.Idx, random.choices(range(1, 32), k=NTESTS))

    AsmInst = fam.get_adt_t(isa.Inst)

    for op, rs1, rs2, rd in zip(ASM.keys(), RS1, RS2, RD):
        inst = ASM[op](rs1, rs2, rd)
        asm_inst = AsmInst(inst)
        res = pe(asm_inst, rs1_v, rs2_v, rd_init).value
        assert res == GOLDS[op](rs1_v, rs2_v).value

