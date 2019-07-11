from .assembler_abc import AbstractAssembler
from hwtypes import AbstractBitVector, BitVector, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple
from hwtypes.adt_meta import BoundMeta, EnumMeta

from types import MappingProxyType
import typing as tp

def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

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
            asm, dsm, width, layout = _sum(isa)
        elif _issubclass(isa, (Bit, BitVector)):
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
        if isinstance(inst.value, int):
            used.add(inst.value)
            i_map[inst] = inst.value
        else:
            assert isinstance(inst.value, EnumMeta.Auto)
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
        layout[field.__name__] = _, w = (tag_width, tag_width + field_width)
        width = max(width, w)

    def assembler(inst):
        v = inst.value
        field = type(v)
        pay_load = Assembler(field)._asm(v)
        opcode = field_2_tag[field]
        opcode |= pay_load << tag_width
        return opcode

    def disassembler(opcode):
        tag = opcode[0:tag_width].as_uint()
        field = tag_2_field[tag]
        pay_load = opcode[slice(*layout[field.__name__])]
        inst = isa(Assembler(field).disassemble(pay_load))
        return inst

    return assembler, disassembler, width, layout

def _field(isa : tp.Type[AbstractBitVector]):
    width = isa.size
    layout = {}
    def assembler(inst):
        return int(inst)
    def disassembler(opcode):
        return isa(opcode)
    return assembler, disassembler, width, layout


