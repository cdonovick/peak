from .assembler_abc import AbstractAssembler
from hwtypes import AbstractBitVector, AbstractBit, BitVector, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple
from hwtypes.adt_meta import BoundMeta, EnumMeta

from types import MappingProxyType
import typing as tp

from .assembler_util import _issubclass

class Assembler(AbstractAssembler):
    _asm : tp.Callable[['isa'], int]
    _dsm : tp.Callable[[int], 'isa']
    _width : int
    _layout : tp.Mapping[str, tp.Tuple[int, int]]

    def __init__(self, isa: BoundMeta):
        super().__init__(isa)
        if _issubclass(isa, Enum):
            asm, dsm, width, layout = _enum(isa)
        elif _issubclass(isa, (Tuple, Product)):
            asm, dsm, width, layout = _tuple(isa)
        elif _issubclass(isa, Sum):
            asm, dsm, width, layout, *tag_args = _sum(isa)
            self._tag_asm = tag_args[0]
            self._tag_dsm = tag_args[1]
            self._tag_width = tag_args[2]
            self._tag_layout = tag_args[3]
        elif _issubclass(isa, (AbstractBit, AbstractBitVector)):
            asm, dsm, width, layout = _field(isa)
        else:
            raise TypeError(f'isa: {isa}')
        self._asm = asm
        self._dsm = dsm
        self._width = width
        self._layout = layout

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
        return self._dsm(opcode)

    def assemble_tag(self, T: type, bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        if not _issubclass(self.isa, Sum):
            raise TypeError('can only assemble tag for Sum')
        elif T not in self.isa:
            raise TypeError(f'{T} is not a member of {self._asm}')
        return bv_type[self.tag_width](self._tag_asm(T))

    def disassemble_tag(self, tag: BitVector) -> 'T':
        if not _issubclass(self.isa, Sum):
            raise TypeError('can only disassemble tag for Sum')
        return self._tag_dsm(tag)

    @property
    def tag_width(self) -> int:
        if not _issubclass(self.isa, Sum):
            raise TypeError('tag_width only for Sum')
        return self._tag_width

    @property
    def tag_layout(self) -> tp.Mapping[str, tp.Tuple[int, int]]:
        if not _issubclass(self.isa, Sum):
            raise TypeError('tag_layout only for Sum')
        return self._tag_layout

    def __repr__(self):
        return f'{type(self)}({self.isa})'


def _enum(isa : Enum) -> int:
    asm = {}
    dsm = {}
    layout = {}

    free  = []
    used  = set()
    i_map = {}
    for inst in isa.enumerate():
        val = inst._value_
        if isinstance(val, int):
            used.add(val)
            i_map[inst] = val
        else:
            assert isinstance(val, EnumMeta.Auto)
            free.append(inst)
    c = 0
    while free:
        inst = free.pop()
        while c in used:
            c += 1
        used.add(c)
        i_map[inst] = c

    width = max(used).bit_length()
    for inst in isa.enumerate():
        layout[inst] = (0, width)
        opcode = i_map[inst]
        asm[inst] = opcode
        dsm[opcode] = inst

    def assembler(inst):
        return asm[inst]

    def disassembler(opcode):
        return dsm[opcode]

    return assembler, disassembler, width, layout


def _tuple(isa : Tuple) -> int:
    layout = {}
    base = 0
    for name,field in isa.field_dict.items():
        field_width = Assembler(field).width
        layout[name] = _, base = (base, base + field_width)

    width = base

    def assembler(inst):
        opcode = 0
        for name,field in isa.field_dict.items():
            assembler = Assembler(field)
            v = assembler._asm(inst.value_dict[name])
            opcode |= v << layout[name][0]
        return opcode

    def disassembler(opcode):
        args = []
        for name,field in isa.field_dict.items():
            idx = slice(*layout[name])
            args.append(Assembler(field).disassemble(opcode[idx]))
        return isa(*args)

    return assembler, disassembler, width, layout


def _sum(isa : Sum) -> int:
    tag_2_field = {}
    field_2_tag = {}
    layout = {}
    tag_width = len(isa.fields).bit_length()

    width = 0
    for tag, field in enumerate(sorted(isa.fields, key=lambda field: (field.__name__, field.__module__))):
        field_width = Assembler(field).width
        tag_2_field[tag] = field
        field_2_tag[field] = tag
        layout[field] = _, w = (tag_width, tag_width + field_width)
        width = max(width, w)

    def assembler(inst):
        v = inst._value_
        field = type(v)
        pay_load = Assembler(field)._asm(v)
        opcode = field_2_tag[field]
        opcode |= pay_load << tag_width
        return opcode

    def disassembler(opcode):
        tag = opcode[0:tag_width].as_uint()
        field = tag_2_field[tag]
        pay_load = opcode[slice(*layout[field])]
        inst = isa(Assembler(field).disassemble(pay_load))
        return inst

    def tag_assembler(T):
        return field_2_tag[T]

    def tag_dissambler(tag):
        return tag_2_field[tag.as_uint()]

    return (assembler, disassembler, width, layout,
            tag_assembler, tag_dissambler, tag_width, (0, tag_width))


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
    return assembler, disassembler, width, layout
