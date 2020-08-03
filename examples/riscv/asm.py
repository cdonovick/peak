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


_LAYOUT_T = tp.Union[isa.R, isa.I, isa.Is, isa.S, isa.U, isa.B, isa.J]
_TAG_T = tp.Union[isa.ArithInst, isa.ShiftInst,
        isa.StoreInst, isa.LoadInst, isa.BranchInst]
_CONSTRUCTOR_T = tp.Callable[[_LAYOUT_T, tp.Optional[_TAG_T]], isa.Inst]

# Generates a constructor function
def _gen(T) -> _CONSTRUCTOR_T:
    attrs = {
        isa.ArithInst: 'arith',
        isa.ShiftInst: 'shift',
    }

    containers = {
        isa.ArithInst: isa.OP_IMM_A,
        isa.ShiftInst: isa.OP_IMM_S,
    }

    if issubclass(T, TaggedUnion):
        assert T is isa.OP_IMM
        def constructor(data: _LAYOUT_T, tag: _TAG_T):
            tag_type = type(tag)
            return T(**{attrs[tag_type]: containers[tag_type](data, tag)})
    elif hasattr(T, 'tag'):
        assert hasattr(T, 'data')
        # case for AluInst
        if issubclass(T.tag, TaggedUnion):
            assert T.tag is isa.AluInst
            def constructor(data: _LAYOUT_T, tag: _TAG_T):
                tag_type = type(tag)
                return T(data, T.tag(**{attrs[tag_type]: tag}))
        else:
            def constructor(data: _LAYOUT_T, tag: _TAG_T):
                return T(data, tag)
    else:
        assert hasattr(T, 'data')
        def constructor(data: _LAYOUT_T, tag: _TAG_T):
            return T(data)

    return constructor


# Given a top level type construct from data/tag
CONSTRUCTORS : tp.Mapping[tp.Type, _CONSTRUCTOR_T] = {
    T: _gen(T) for T in isa.Inst.field_dict
}


IMM_BITS = {
    isa.I : (0, 12),
    isa.Is : (0, 5),
    isa.S: (0, 12),
    isa.U: (12, 32),
    isa.B: (1, 13),
    isa.J: (1, 21),
}


def _unpack(inst: isa.Inst) -> tp.Tuple[
            _LAYOUT_T,
            tp.Optional[_TAG_T],
            tp.Type, # The matching type
        ]:
    for T in isa.Inst.field_dict:
        if inst[T].match:
            inst_ = inst[T].value
            # case for OP_IMM
            if issubclass(T, TaggedUnion):
                assert T is isa.OP_IMM
                for attr, S in T.field_dict.items():
                    m = getattr(inst_, attr)
                    if m.match:
                        inst_ = m.value
                        break
                else:
                    # Should always break
                    raise AssertionError('Unreachable code')

            assert hasattr(inst_, 'data')
            data = inst_.data
            if hasattr(inst_, 'tag'):
                tag = inst_.tag
                # case for AluInst
                if isinstance(tag, TaggedUnion):
                    tag_type = type(tag)
                    assert tag_type is isa.AluInst
                    for attr in tag_type.field_dict:
                        m = getattr(tag, attr)
                        if m.match:
                            tag = m.value
                            break
                    else:
                        # Should always break
                        raise AssertionError('Unreachable code')
            else:
                assert not hasattr(inst_, 'tag')
                tag  = None

            return data, tag, T
    # Should have returned
    raise AssertionError('Unreachable code')


def set_fields(
        inst: isa.Inst,
        rs1: tp.Optional[int] = None,
        rs2: tp.Optional[int] = None,
        rd: tp.Optional[int] = None,
        imm: tp.Optional[int] = None,
        ) -> isa.Inst:

    # Unpack the data
    data, tag, inst_type = _unpack(inst)
    data_type = type(data)

    constructor = CONSTRUCTORS[inst_type]

    FIELDS = dict(rs1=rs1, rs2=rs2, rd=rd, imm=imm)
    kwargs = {}

    # validate arguments
    for field_name, field_value in FIELDS.items():
        field_type = getattr(data_type, field_name, None)

        if field_value is not None:
            if field_type is None:
                raise ValueError(f'instruction {data_type} has no {field_name} field')

            if field_value < 0:
                raise ValueError('Values for fields must be unsigned (positive)')

            if field_name == 'imm':
                field_bits = IMM_BITS[data_type]
            else:
                field_bits = (0, field_type.size)

            #ensure bottom bits are 0
            if field_value % (1 << field_bits[0]) != 0:
                raise ValueError(f'{field_name} can not store value, bottom bits would be truncated')

            #ensure value fits in field
            if field_value % (1 << field_bits[1]) != field_value:
                raise ValueError(f'{field_name} can not store value, top bits would be truncated')

            kwargs[field_name] = field_type(field_value >> field_bits[0])
        elif field_type is not None:
            kwargs[field_name] = getattr(data, field_name)


    data = data_type(**kwargs)
    sub_inst = constructor(data, tag)
    assert isinstance(sub_inst, inst_type)
    new_inst = isa.Inst(sub_inst)
    return new_inst


def get_fields(inst: isa.Inst) -> tp.Mapping[str, tp.Optional[int]]:
    data, *_ = _unpack(inst)
    data_type = type(data)
    kwargs = dict(rs1=None, rs2=None, rd=None, imm=None)
    for field_name, field_type in data_type.field_dict.items():
        field_value = getattr(data, field_name).as_uint()

        if field_name == 'imm':
            field_value <<= IMM_BITS[data_type][0]
        assert field_name in kwargs
        kwargs[field_name] = field_value
    return kwargs
