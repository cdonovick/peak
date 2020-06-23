from examples.riscv import sim as sim_mod, isa as isa_mod, family

def test_riscv():
    R32I, isa = sim_mod.R32I_fc.Py
    riscv = R32I()

    pc = isa.Word(0)
    r0 = isa.Idx(0)
    rs1 = isa.Idx(1)
    rs2 = isa.Idx(2)
    rd  = isa.Idx(3)

    riscv.register_file.store(rs1, isa.Word(5))
    riscv.register_file.store(rs2, isa.Word(6))

    assert riscv.register_file.load1(r0) == isa.Word(0)
    assert riscv.register_file.load2(r0) == isa.Word(0)

    assert riscv.register_file.load1(rs1) == isa.Word(5)
    assert riscv.register_file.load2(rs1) == isa.Word(5)

    assert riscv.register_file.load1(rs2) == isa.Word(6)
    assert riscv.register_file.load2(rs2) == isa.Word(6)

    data  = isa.R(rd=rd, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(isa.ArithInst.ADD)
    alur = isa.ALUR(data=data, tag=tag)
    alu_inst = isa.ALU(r=alur)
    inst = isa.Inst(alu=alu_inst)

    pc_next = riscv(inst, pc)

    assert pc_next == isa.Word(4)
    assert riscv.register_file.load1(rd) == riscv.register_file.load2(rd) == isa.Word(11)

def test_riscv_smt():
    fam = family.SMTFamily()
    R32I, _ = sim_mod.R32I_mappable_fc(fam)
    isa = isa_mod.ISA_fc.Py

    riscv = R32I()

    rs1_v = fam.Word(name='rs1')
    rs2_v = fam.Word(name='rs2')
    rd_init = fam.Word(name='rd_init')
    pc = fam.Word(name='pc')

    riscv._set_rd_(rd_init)

    r0 = isa.Idx(0)
    rs1 = isa.Idx(1)
    rs2 = isa.Idx(2)
    rd  = isa.Idx(3)
    data  = isa.R(rd=rd, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(isa.ArithInst.SUB)
    alur = isa.ALUR(data=data, tag=tag)
    alu_inst = isa.ALU(r=alur)
    inst = isa.Inst(alu=alu_inst)

    asm_Inst = fam.get_adt_t(isa.Inst)
    asm_inst = asm_Inst(inst)
    pc_next, rd = riscv(asm_inst, pc, rs1_v, rs2_v)

    # Recall pysmt == is structural equiv
    assert pc_next.value == (pc.value + 4)
    assert rd.value == (rs1_v.value - rs2_v.value)
    assert rd.value != rd_init.value

    riscv._set_rd_(rd_init)

    # setting rd=r0 makes this a nop
    data  = isa.R(rd=r0, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(isa.ArithInst.SUB)
    alur = isa.ALUR(data=data, tag=tag)
    alu_inst = isa.ALU(r=alur)
    inst = isa.Inst(alu=alu_inst)
    asm_Inst = fam.get_adt_t(isa.Inst)
    asm_inst = asm_Inst(inst)

    pc_next, rd = riscv(asm_inst, pc, rs1_v, rs2_v)
    assert pc_next.value == (pc.value + 4)
    assert rd.value != (rs1_v.value - rs2_v.value)
    assert rd.value == rd_init.value
