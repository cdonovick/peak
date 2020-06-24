from collections import defaultdict
import functools as ft
import operator
from types import MappingProxyType
import typing as tp


from .assembler_abc import AbstractAssembler
from hwtypes import AbstractBitVector, AbstractBit, BitVector, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple, TaggedUnion
from hwtypes.adt_meta import BoundMeta, EnumMeta


from .assembler_util import _issubclass, _gen_is_valid

class Assembler(AbstractAssembler):
    _asm : tp.Callable[['isa'], int]
    _dsm : tp.Callable[[int], 'isa']
    _width : int
    _layout : tp.Mapping[str, tp.Tuple[int, int]]

    def __init__(self, isa: BoundMeta):
        super().__init__(isa)
        if _issubclass(isa, Enum):
            asm, dsm, isv, width, layout = _enum(isa)
        elif _issubclass(isa, (Tuple, Product)):
            asm, dsm, isv, width, layout = _tuple(isa)
        elif _issubclass(isa, Sum):
            asm, dsm, isv, width, layout, *tag_args = _sum(isa)
            self._tag_asm = tag_args[0]
            self._tag_dsm = tag_args[1]
            self._tag_isv = tag_args[2]
            self._tag_width = tag_args[3]
            self._tag_layout = tag_args[4]
        elif _issubclass(isa, (AbstractBit, AbstractBitVector)):
            asm, dsm, isv, width, layout = _field(isa)
        else:
            raise TypeError(f'isa: {isa}')
        self._asm = asm
        self._dsm = dsm
        self._width = width
        self._layout = layout
        self._isv = isv

    @property
    def width(self) -> int:
        return self._width

    @property
    def layout(self) -> tp.Mapping[str, tp.Tuple[int, int]]:
        return MappingProxyType(self._layout)

    def assemble(self,
            inst: 'isa',
            bv_type: tp.Type[AbstractBitVector] = BitVector) -> 'bv_type':
        opcode = self._asm(inst)
        assert opcode.bit_length() <= self.width, (opcode, self.width)
        return bv_type[self.width](opcode)

    def disassemble(self, opcode: BitVector) -> 'isa':
        if not self.is_valid(opcode):
            raise ValueError(f'invalid opcode: {opcode}')
        return self._dsm(opcode)

    def is_valid(self, opcode: AbstractBitVector):
        return self._isv(opcode)

    def assemble_tag(self, T: tp.Union[type, str], bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        if not _issubclass(self.isa, Sum):
            raise TypeError('can only assemble tag for Sum')
        return bv_type[self.tag_width](self._tag_asm(T))

    def disassemble_tag(self, tag: BitVector) -> tp.Union['T', str]:
        if not _issubclass(self.isa, Sum):
            raise TypeError('can only disassemble tag for Sum')
        if not self.is_valid_tag(tag):
            raise ValueError(f'invalid tag: {opcode}')
        return self._tag_dsm(tag)

    def is_valid_tag(self, tag: AbstractBitVector) -> AbstractBit:
        if not _issubclass(self.isa, Sum):
            raise TypeError('can only validate tag for Sum')
        return self._tag_isv(tag)

    @property
    def tag_width(self) -> int:
        if not _issubclass(self.isa, Sum):
            raise TypeError('tag_width only for Sum')
        return self._tag_width

    @property
    def tag_layout(self) -> tp.Tuple[int, int]:
        if not _issubclass(self.isa, Sum):
            raise TypeError('tag_layout only for Sum')
        return self._tag_layout

    def __repr__(self):
        return f'{type(self)}({self.isa})'


def _enum(isa: tp.Type[Enum]) -> int:
    asm: tp.Dict[Enum, int] = {}
    dsm: tp.Dict[int, Enum] = {}
    layout: tp.Dict[Enum, tp.Tuple[int, int]] = {}

    free  = []
    used = set()

    for inst in isa.enumerate():
        val = inst._value_
        if isinstance(val, int):
            if (val < 0):
                raise ValueError('Enum values must be > 0')
            asm[inst] = val
            dsm[val] = inst
            used.add(val)
        else:
            assert isinstance(val, EnumMeta.Auto)
            free.append(inst)

    c = 0
    for i in free:
        while c in used:
            c += 1
        used.add(c)
        asm[i] = c
        dsm[c] = i

    if not asm:
        raise TypeError('Enum must not be empty')

    opcodes = asm.values()

    width = max(opcodes).bit_length()

    for inst in isa.enumerate():
        layout[inst] = (0, width)

    assemble = asm.__getitem__
    disassemble = dsm.__getitem__
    is_valid = _gen_is_valid(opcodes, width)
    return assemble, disassemble, is_valid, width, layout


def _tuple(isa: tp.Type[Tuple]):
    layout = {}
    base = 0
    for name, field in isa.field_dict.items():
        field_width = Assembler(field).width
        layout[name] = _, base = (base, base + field_width)

    width = base

    def assemble(inst: isa) -> int:
        opcode = 0
        for name, field in isa.field_dict.items():
            assembler = Assembler(field)
            v = assembler._asm(inst.value_dict[name])
            opcode |= v << layout[name][0]
        return opcode

    def disassemble(opcode: BitVector[width]) -> isa:
        args = []
        for name,field in isa.field_dict.items():
            idx = slice(*layout[name])
            args.append(Assembler(field).disassemble(opcode[idx]))
        return isa(*args)

    def is_valid(opcode: AbstractBitVector[width]) -> AbstractBit:
        args = []
        for name, field in isa.field_dict.items():
            idx = slice(*layout[name])
            args.append(Assembler(field).is_valid(opcode[idx]))
        return ft.reduce(operator.and_, args, opcode.get_family().Bit(1))

    return assemble, disassemble, is_valid, width, layout


def _sum(isa: tp.Type[Sum]):
    name_to_field = {}
    name_to_tag = {}
    tag_to_name = {}
    # Tracks all the tags associated with a given field type
    # which may not be 1-1 in TaggedUnion
    field_to_tags = defaultdict(list)
    layout = {}
    tag_width = (len(isa.field_dict)-1).bit_length()
    tag_layout = (0, tag_width)

    sorted_fields = list(sorted(
        isa.field_dict.items(),
        key=repr
    ))

    payload_width = 0
    for tag, (name, field) in enumerate(sorted_fields):
        assert name not in name_to_field
        name_to_field[name] = field
        name_to_tag[name] = tag
        tag_to_name[tag] = name
        field_to_tags[field].append(tag)
        if field not in layout:
            assert len(field_to_tags[field]) == 1
            field_width = Assembler(field).width
            layout[field] = (tag_width, tag_width + field_width)
            layout[name] = (tag_width, tag_width + field_width)
            payload_width = max(payload_width, field_width)
        elif name not in layout:
            layout[name] = layout[field]

    max_tag = tag
    width = tag_width + payload_width

    tag_validators = {}
    for field, tags in field_to_tags.items():
        tag_validators[field] = _gen_is_valid(tags, tag_width)

    def assemble(inst: isa) -> int:
        for k, v in inst.value_dict.items():
            if v is not None:
                break
        else:
            raise AssertionError(f'Unreachable code, {inst} has no value')

        assert name_to_field[k] == type(v)
        field = type(v)
        payload = Assembler(field)._asm(v)
        tag = name_to_tag[k]
        opcode = (payload << tag_width) | tag
        return opcode

    def disassemble(opcode: BitVector[width]) -> isa:
        tag = opcode[0:tag_width].as_uint()
        name = tag_to_name[tag]
        field = name_to_field[name]
        payload = opcode[slice(*layout[field])]
        value = Assembler(field).disassemble(payload)
        value_dict = {k: value if k == name else None for k in isa.field_dict}
        return isa.from_values(value_dict)


    def is_valid(opcode: AbstractBitVector[width]) -> AbstractBit:
        tag = opcode[0:tag_width]
        valid = opcode.get_family().Bit(0)
        for field, validator in tag_validators.items():
            payload = opcode[slice(*layout[field])]
            valid_field = Assembler(field).is_valid(payload)
            valid_tag = validator(tag)
            valid |= (valid_tag & valid_field)
        return valid


    tag_assemble = name_to_tag.__getitem__
    tag_diasssamble = tag_to_name.__getitem__
    tag_is_valid = _gen_is_valid(tag_to_name.keys(), tag_width)
    return (assemble, disassemble, is_valid, width, layout,
            tag_assemble, tag_diasssamble, tag_is_valid, tag_width, tag_layout)


def _field(isa : tp.Type[AbstractBitVector]):
    if _issubclass(isa, AbstractBitVector):
        width = isa.size
    elif _issubclass(isa, AbstractBit):
        width = 1
    else:
        raise TypeError()

    layout = {}

    def assembler(inst):
        return int(inst)

    def disassembler(opcode):
        return isa(opcode)

    def is_valid(opcode):
        return opcode.get_family().Bit(1)

    return assembler, disassembler, is_valid, width, layout
