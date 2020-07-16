from collections import namedtuple
import typing as tp

from hwtypes.adt import TaggedUnion

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
    if inst_name == 'SUB':
        continue
    f_str = ASM_TEMPLATE.format(
            INST_NAME=inst_name,
            LAYOUT='I',
            OP_T='OP_IMM_A',
            TAG_T='ArithInst',
            TAG_KW='arith',
        )

    exec(f_str)


for inst_name in isa.ShiftInst._field_table_:
    f_str = ASM_TEMPLATE.format(
            INST_NAME=inst_name,
            LAYOUT='Is',
            OP_T='OP_IMM_S',
            TAG_T='ShiftInst',
            TAG_KW='shift',
        )

    exec(f_str)


# special case asm_SUB because there is no SUBI instruction
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


IMM_BITS = {
    isa.I : (0, 12),
    isa.Is : (0, 5),
    isa.S: (0, 12),
    isa.U: (12, 32),
    isa.B: (1, 13),
    isa.J: (1, 21),
}



def set_fields(
        inst: isa.Inst,
        rs1: tp.Optional[int] = None,
        rs2: tp.Optional[int] = None,
        rd: tp.Optional[int] = None,
        imm: tp.Optional[int] = None,
        ) -> isa.Inst:

    # Unpack the data
    for T in isa.Inst.field_dict:
        if inst[T].match:
            inst_ = inst[T].value
            constructor = T
            # case for OP_IMM
            if issubclass(T, TaggedUnion):
                assert T is isa.OP_IMM
                for attr, S in T.field_dict.items():
                    m = getattr(inst_, attr)
                    if m.match:
                        constructor = lambda data, tag: T(**{attr: S(data, tag)})
                        inst_ = m.value
                        break

            if hasattr(inst_, 'data'):
                assert hasattr(inst_, 'tag')
                data = inst_.data
                tag = inst_.tag
            else:
                assert not hasattr(inst_, 'tag')
                constructor = lambda data, tag: T(data)
                data = inst_
                tag  = None
            break

    FIELDS = dict(rs1=rs1, rs2=rs2, rd=rd, imm=imm)
    Data = type(data)

    kwargs = {}

    # validate arguments
    for field_name, field_value in FIELDS.items():
        Field = getattr(Data, field_name, None)

        if field_value is not None:
            if Field is None:
                raise ValueError(f'instruction {Data} has no {field_name} field')

            if field_value < 0:
                raise ValueError('Values for fields must be unsigned (positive)')

            if field_name == 'imm':
                field_bits = IMM_BITS[Data]
            else:
                field_bits = (0, Field.size)

            #ensure bottom bits are 0
            if field_value % (1 << field_bits[0]) != 0:
                raise ValueError('Field can not store value, bottom bits would be truncated')

            #ensure value fits in field
            if field_value % (1 << field_bits[1]) != field_value:
                raise ValueError('Field can not store value, top bits would be truncated')

            kwargs[field_name] = Field(field_value >> field_bits[0])
        elif Field is not None:
            kwargs[field_name] = getattr(data, field_name)


    data = Data(**kwargs)
    sub_inst = constructor(data, tag)
    new_inst = isa.Inst(sub_inst)
    return new_inst
