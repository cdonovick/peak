from examples.riscv import sim, isa, family

def test_riscv():
    R32I, RF, isa = sim.R32I_fc.Py

    register_file = RF()
    pc = isa.Word(0)
    r0 = isa.Idx(0)
    rs1 = isa.Idx(1)
    rs2 = isa.Idx(2)
    rd  = isa.Idx(3)

    register_file.store(isa.Idx(1), isa.Word(5))
    register_file.store(isa.Idx(2), isa.Word(6))

    assert register_file.load1(r0) == register_file.load2(r0) == isa.Word(0)
    assert register_file.load1(rs1) == register_file.load2(rs1) == isa.Word(5)
    assert register_file.load1(rs2) == register_file.load2(rs2) == isa.Word(6)

    riscv = R32I()

    data  = isa.R(rd=rd, rs1=rs1, rs2=rs2)
    tag = isa.AluInst(isa.ArithInst.ADD)
    alur = isa.ALUR(data=data, tag=tag)
    alu_inst = isa.ALU(r=alur)
    inst = isa.Inst(alu=alu_inst)

    pc_next = riscv(inst, pc, register_file)

    assert pc_next == isa.Word(4)
    assert register_file.load1(rd) == register_file.load2(rd) == isa.Word(11)
