from .assembler_abc import AbstractAssembler
from hwtypes import AbstractBitVector, BitVector, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple
from hwtypes.adt_meta import BoundMeta

from types import MappingProxyType
import typing as tp

class Assembler(AbstractAssembler):
    _asm : tp.Mapping['isa', int]
    _dsm : tp.Mapping[int, 'isa']
    _width : int
    _layout : tp.Mapping[str, tp.Tuple[int, int]]

    def __init__(self, isa: BoundMeta):
        super().__init__(isa)
        if _issubclass(isa, enum):
            asm, dsm, width, layout = _enum(isa)
        elif _issubclass(isa, (Tuple, Product)):
            asm, dsm, width, layout = _tuple(isa)
        elif _issubclass(isa, Sum):
            asm, dsm, width, layout = _sum(isa)
        elif _issubclass(isa, (Bit, BitVector)):
            asm, dsm, width, layout = _field(isa)
        else:
            raise TypeError()

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
        opcode = self._asm[inst]
        assert opcode.bit_length() <= self.width
        return bv_type[self.width](opcode)

    def disassemble(self, opcode: BitVector) -> 'isa':
        opcode = opcode.as_uint()
        return self._dsm[opcode]


def _enum(isa : Enum):
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

    return assembler, disassembler, width, layout

def _tuple(isa : Tuple):
    pass

def _sum(isa : Sum):
    pass

def _field(isa : tp.Type[AbstractBitVector]):
    pass
