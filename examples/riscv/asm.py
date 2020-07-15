import typing as tp

from .isa import ISA_fc

isa = ISA_fc.Py


ASM_TEMPLATE = '''\
def asm_{INST_NAME}(rs1, rd, rs2=None, imm=None):
    if imm is not None and rs2 is not None:
        raise ValueError('May not specify both rs2 and imm')
    elif imm is None and rs2 is None:
        raise ValueError('Must specify either rs2 or imm')

    rs1 = isa.Idx(rs1)
    rd = isa.Idx(rd)
    if imm is not None:
        imm = isa.{LAYOUT}.imm(imm)
        data = isa.{LAYOUT}(rs1=rs1, rd=rd, imm=imm)
        T = lambda data, tag: isa.OP_IMM({TAG_KW}=isa.{OP_T}(data, tag))
        tag = isa.{TAG_T}.{INST_NAME}
    else:
        rs2 = isa.Idx(rs2)
        data = isa.R(rs1=rs1, rs2=rs2, rd=rd)
        T = isa.OP
        tag = isa.AluInst({TAG_KW}=isa.{TAG_T}.{INST_NAME})
    return isa.Inst(T(data, tag))
'''


for inst_name in isa.ArithInst._field_table_:
    f_str = ASM_TEMPLATE.format(
            INST_NAME=inst_name,
            LAYOUT='I',
            OP_T='OP_IMM_A',
            TAG_T='ArithInst',
            TAG_KW='arith',
        )

    exec(f_str)

# redefine asm_SUB because there is no SUBI instruction
def asm_SUB(rs1, rd, rs2=None, imm=None):
    if imm is not None and rs2 is not None:
        raise ValueError('May not specify both rs2 and imm')
    elif imm is None and rs2 is None:
        raise ValueError('Must specify either rs2 or imm')

    rs1 = isa.Idx(rs1)
    rd = isa.Idx(rd)
    if imm is not None:
        imm = -isa.I.imm(imm)
        data = isa.I(rs1=rs1, rd=rd, imm=imm)
        T = lambda data, tag: isa.OP_IMM(arith=isa.OP_IMM_A(data, tag))
        tag = isa.ArithInst.ADD
    else:
        rs2 = isa.Idx(rs2)
        data = isa.R(rs1=rs1, rs2=rs2, rd=rd)
        T = isa.OP
        tag = isa.AluInst(arith=isa.ArithInst.SUB)
    return isa.Inst(T(data, tag))


for inst_name in isa.ShiftInst._field_table_:
    f_str = ASM_TEMPLATE.format(
            INST_NAME=inst_name,
            LAYOUT='Is',
            OP_T='OP_IMM_S',
            TAG_T='ShiftInst',
            TAG_KW='shift',
        )

    exec(f_str)

def set_fields(
        inst: isa.Inst,
        rs1: tp.Optional[int] = None,
        rs2: tp.Optional[int] = None,
        rd: tp.Optional[int] = None,
        imm: tp.Optional[int] = None,
        ) -> isa.Inst:

    if inst[isa.OP].match:
        T = isa.OP
        data = inst[isa.OP].value.data
        tag = inst[isa.OP].value.tag
    elif inst[isa.OP_IMM].match:
        inst_ = inst[isa.OP_IMM].value
        if inst_[isa.OP_IMM_A].match:
            T = lambda data, tag: isa.OP_IMM(arith=isa.OP_IMM_A(data, tag))
            inst_ = inst_[isa.OP_IMM_A].value
        else:
            assert inst_[isa.OP_IMM_S].match
            T = lambda data, tag: isa.OP_IMM(shift=isa.OP_IMM_S(data, tag))
            inst_ = inst_[isa.OP_IMM_S].value
        data = inst_.data
        tag = inst_.tag
    elif inst[isa.LUI].match:
        T = lambda data, tag: isa.LUI(data)
        data = inst[isa.LUI].value
        tag = None
    elif inst[isa.AUIPC].match:
        T = lambda data, tag: isa.AUIPC(data)
        data = inst[isa.AUIPC].value
        tag = None
    elif isnt[isa.JAL].match:
        T = lambda data, tag: isa.JAL(data)
        data = inst[isa.JAL].value
        tag = None
    elif inst[isa.JALR].match:
        T = lambda data, tag: isa.JALR(data)
        data = inst[isa.JALR].value
        tag = None
    elif inst[isa.Branch].match:
        T = isa.Branch
        data = inst[isa.Branch].value.data
        tag = inst[isa.Branch].value.tag
    elif inst[isa.Load].match:
        T = isa.Load
        data = inst[isa.Load].value.data
        tag = inst[isa.Load].value.tag
    elif inst[isa.Store].match:
        T = isa.Store
        data = inst[isa.Store].value.data
        tag = inst[isa.Store].value.tag
    else:
        raise AssertionError(f'Unreachable code, inst: {inst} :: {type(inst)}')

    # validate arguments
    if isinstance(data, isa.R):
        if imm is not None:
            raise ValueError('R type instruction has no imm field')
    elif isinstance(data, isa.I):
        if rs2 is not None:
            raise ValueError('I type instruction has no rs2 field')
        if imm is not None and not (0 <= imm < (1 << isa.I.imm.size)):
            raise ValueError('invalid imm')

    elif isinstance(data, isa.Is):
        if rs2 is not None:
            raise ValueError('Is type instruction has no rs2 field')
        if imm is not None and not (0 <= imm < (1 << isa.Is.imm.size)):
            raise ValueError('invalid imm')

    elif isinstance(data, isa.S):
        if rd is not None:
            raise ValueError('S type instruction has no rd field')
        if imm is not None and not (0 <= imm < (1 << isa.S.imm.size)):
            raise ValueError('invalid imm')

    elif isinstance(data, isa.U):
        if (rs1 or rs2) is not None:
            raise ValueError('U type instruction has no rs* field')
        if imm is not None:
            if imm < 0:
                raise ValueError('invalid imm')
            bottom_bits = imm % (1 << 12)
            if bottom_bits != 0:
                raise ValueError('invalid imm')
            imm = imm >> 12
            if imm >= (1 << isa.U.imm.size):
                raise ValueError('invalid imm')

    elif isinstance(data, isa.B):
        if rd is not None:
            raise ValueError('B type instruction has no rd field')
        if imm is not None:
            if imm < 0:
                raise ValueError('invalid imm')
            bottom_bits = imm % 2
            if bottom_bits != 0:
                raise ValueError('invalid imm')

            imm = imm >> 1
            if imm >= (1 << isa.B.imm.size):
                raise ValueError('invalid imm')

    elif isinstance(data, isa.J):
        if (rs1 or rs2) is not None:
            raise ValueError('J type instruction has no rs* field')
        if imm is not None:
            if imm < 0:
                raise ValueError('invalid imm')
            bottom_bits = imm % 2
            if bottom_bits != 0:
                raise ValueError('invalid imm')

            imm = imm >> 1
            if imm >= (1 << isa.J.imm.size):
                raise ValueError('invalid imm')
    else:
        raise AssertionError(f'Unreachable code, data: {data} :: {type(data)}')

    kwargs = {}
    for k, v in (('rs1', rs1), ('rs2', rs2), ('rd', rd), ('imm', imm)):
        field = getattr(type(data), k, None)
        if field:
            if v is not None:
                kwargs[k] = field(v)
            else:
                kwargs[k] = getattr(data, k)

    data = type(data)(**kwargs)
    new_inst = isa.Inst(T(data, tag))
    return new_inst



