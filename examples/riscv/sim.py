
from .isa import ISA_fc
from peak import Peak, name_outputs, family_closure, Const

@family_closure
def R32I_fc(family):
    Bit = isa.Bit
    BitVector = isa.BitVector
    Unsigned = isa.Unsigned
    Signed = isa.Signed
    Word = BitVector[32]

    isa = ISA_fc(family)

    ExecInst = family.get_constructor(isa.AluInst)

    @family.assemble(locals(), globals())
    class R32I(Peak):
        @name_outputs(out=Word, pc_next=Word)
        def __call__(self, inst: isa.ExpandInst, pc: Word) -> (Word, Word):
            # Decode
            # Inputs:
            #   inst, pc
            # Outputs:
            #   a, b, exec_inst,
            #   lsb_mask, is_branch, is_jump
            #   branch_offset, cmp_zero, invert
            lsb_mask = Word(-1)
            is_branch = Bit(0)
            is_jump = Bit(0)
            branch_offset = Word(0)
            cmp_zero = Bit(0)
            invert = Bit(0)

            if inst.alu.match:
                alu_inst = inst.alu.value
                if alu_inst.i.match:
                    i_inst = alu_inst.i.value
                    a = i_inst.data.rs1
                    b = i_inst.data.imm.sext(20)
                    exec_inst = ExecInst(isa.ArithInst, i_inst.tag)
                elif alu_inst.s.match:
                    s_inst = alu_inst.s.value
                    a = s_inst.data.rs1
                    b = s_inst.data.imm.sext(27)
                    exec_inst = ExecInst(isa.ShftInst, s_inst.tag)
                elif alu_inst.r.match:
                    r_inst = alu_inst.r.value
                    a = r_inst.data.rs1
                    b = r_inst.data.rs2
                    exec_inst = r_inst.tag
                else:
                    assert alu_inst.u.match
                    u_inst = alu_inst.u.value
                    if u_inst.tag == isa.PCInst.LUI:
                        a = Word(0)
                    else:
                        assert u_inst.tag == isa.PCInst.AUIPC
                        a = pc
                    b = u_inst.data.imm.sext(12) << 12
                    exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.ADD)
            elif inst.ctrl.match:
                ctrl_inst = inst.ctrl.value
                if ctrl_inst.j.match:
                    j_inst = ctrl_inst.j.value
                    is_jump = Bit(1)
                    if j_inst[isa.JAL].match:
                        jal_inst = j_inst[isa.JAL].value
                        a = pc
                        b = jal_inst.imm.sext(12) << 1
                    else:
                        assert j_inst[isa.JALR].match
                        jalr_inst = j_inst[isa.JALR].value
                        a = jalr_inst.rs1
                        b = jalr_inst.imm.sext(20)
                        lsb_mask = ~Word(1)
                    exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.ADD)
                else:
                    assert ctrl_inst.b.match
                    b_inst = ctrl_inst.b.value
                    is_branch = Bit(1)
                    a = b_inst.data.rs1
                    b = b_inst.data.rs2
                    branch_offset = b_inst.data.imm.sext(20) << 1

                    # hand coded common sub-expr elimin
                    is_eq = b_inst.tag == isa.BranchInst.BEQ
                    is_ne = b_inst.tag == isa.BranchInst.BNE
                    is_bge = (b_inst.tag == isa.BranchInst.BGE
                    is_signed = (is_bge | b_inst.tag == isa.BranchInst.BLT)
                    cmp_ge = (is_bge | b_inst.tag == isa.BranchInst.BGEU)

                    if (is_eq | is_ne):
                        exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.XOR)
                        cmp_zero = Bit(1)
                        invert = is_ne
                    else:
                        if is_signed:
                            exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.SLT)
                        else:
                            exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.SLTU)
                        invert = cmp_ge
            else:
                assert inst.mem.match
                a = Word(0)
                b = Word(0)
                exec_inst = ExecInst(isa.ArithInst, isa.ArithInst.ADD)

            # Execute
            # Inputs:
            #   a, b, exec_inst, lsb_mask, branch_offset
            # Outputs:
            #  c, branch_target
            branch_target = pc + branch_offset
            if exec_inst[isa.ArithInst].match:
                arith_inst = exec_inst[isa.ArithInst].value
                if arith_inst == isa.ArithInst.ADD:
                    c = a + b
                elif arith_inst == isa.ArithInst.SUB:
                    c = a - b
                elif arith_inst == isa.ArithInst.SLT:
                    c = Word(a.bvslt(b))
                elif arith_inst == isa.ArithInst.SLTU:
                    c = Word(a.bvult(b))
                elif arith_inst == isa.ArithInst.AND:
                    c = a & b
                elif arith_inst == isa.ArithInst.OR:
                    c = a | b
                else:
                    assert arith_inst == isa.ArithInst.XOR
                    c = a ^ b
            else:
                assert exec_inst[isa.ShftInst].match
                shft_inst = exec_inst[isa.ShftInst].value
                if shft_inst == isa.ShftInst.SLL:
                    c = a.bvshl(b)
                elif shft_inst == isa.ShftInst.SRL:
                    c = a.bvlshr(b)
                else:
                    assert shft_inst == isa.ShftInst.SRA
                    c = a.bvashr(b)

            c = c & lsb_mask # clear bottom bit for jalr

            # Commit
            # Inputs:
            #   pc, c, is_branch, is_jump
            #   branch_target, cmp_zero, invert
            # Outputs:
            #   out, pc_next
            assert not (is_jump & is_branch)
            pc_next = pc+4
            if is_branch:
                out = Word(0)
                if cmp_zero:
                    cond = (c == 0)
                else:
                    cond = c[0]

                cond = cond ^ invert
                if cond:
                    pc_next = branch_target

            elif is_jump:
                out = pc_next
                pc_next = c
            else:
                out = c

            return (out, pc_next)

    return R32I
