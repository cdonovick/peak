from abc import ABCMeta, abstractmethod
import typing as tp
import warnings
import weakref

from hwtypes import AbstractBit, AbstractBitVector, BitVector
from hwtypes.adt import Enum, Product, Sum, Tuple
from hwtypes.adt_meta import BoundMeta, GetitemSyntax, AttrSyntax

from .assembler_util import _issubclass

# Basically just handles instance caching
class AssemblerMeta(ABCMeta):
    # cls -> ((init args -> object) | None)
    _cache = dict()
    def __new__(mcs, name, bases, namespace, cache=True, **kwargs):
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __init__(cls, name, bases, namespace, cache=True, **kwargs):
        if cache:
            type(cls)._cache[cls] = dict()
        else:
            type(cls)._cache[cls] = None

        return super().__init__(name, bases, namespace, **kwargs)

    def __call__(cls, *args, **kwargs):
        i_cache = type(cls)._cache[cls]
        if i_cache is not None:
            idx = (args, tuple(kwargs.items()))
            try:
                return i_cache[idx]
            except KeyError:
                pass
            obj = super().__call__(*args, **kwargs)
            i_cache[idx] = obj
        else:
            obj = super().__call__(*args, **kwargs)

        return obj

class AbstractAssembler(metaclass=AssemblerMeta):
    _isa : BoundMeta

    def __init__(self, isa: BoundMeta):
        self._isa = isa


    def __init_subclass__(cls, cache=True, **kwargs):
        super().__init_subclass__(**kwargs)

    @property
    def isa(self):
        return self._isa

    @property
    def sub(self) -> 'Sub':
        return Sub(self)

    @property
    @abstractmethod
    def width(self) -> int:
        pass

    @property
    @abstractmethod
    def layout(self) -> tp.Mapping[str, tp.Tuple[int, int]]:
        pass

    @abstractmethod
    def assemble(self, inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        pass

    @abstractmethod
    def disassemble(self, opcode: BitVector) -> 'isa':
        pass

    @abstractmethod
    def is_valid(self, opcode: AbstractBitVector) -> AbstractBit:
        pass

    @abstractmethod
    def assemble_tag(self, T: type, bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        pass

    @abstractmethod
    def disassemble_tag(self, opcode: BitVector) -> 'T':
        pass

    @abstractmethod
    def is_valid_tag(self, tag: AbstractBitVector) -> AbstractBit:
        pass

    @property
    @abstractmethod
    def tag_width(self) -> int:
        pass

    @property
    @abstractmethod
    def tag_layout(self) -> tp.Tuple[int, int]:
        pass

class Sub(tp.Mapping):
    _reserved_names = ('asm', 'idx', 'tag_idx', '_asm', '_offset', '_path')

    def __init__(self, assembler, offset=0, path=None):
        isa = assembler.isa
        if isinstance(isa, AttrSyntax):
            for name in type(self)._reserved_names:
                if name in isa.field_dict:
                    warnings.warn(f'field {name} is used by the assembler '
                                   'machinery gettattr access will not work')
        elif not (
                isinstance(isa, GetitemSyntax)
                or _issubclass(isa, (AbstractBit, AbstractBitVector))):
            raise TypeError(f'Unsported type {isa}')

        self._asm = assembler
        self._offset = offset
        if path is None:
            self._path = [f'{self.asm.isa}.sub']
        else:
            self._path = path


    def __getattr__(self, attr):
        return self._get(attr, AttributeError)

    def __getitem__(self, path):
        if not isinstance(path, tuple):
            path = path,
        elif not path:
            # empty path
            return self

        return self._get(path[0], KeyError)[path[1:]]

    def _get(self, attr, Error):
        isa = self.asm.isa

        try:
            field = isa.field_dict[attr]
        except KeyError:
            raise Error(f'Bad path {attr} for {isa}') from None

        sub_asm = type(self.asm)(field)
        offset = self._offset + self.asm.layout[attr][0]
        return type(self)(sub_asm, offset, self._path + [attr])

    def __iter__(self):
        isa = self.asm.isa
        yield from isa.field_dict

    def __len__(self):
        return len(self.asm.isa.fields)


    def __repr__(self):
        path = '.'.join(self._path)
        return path

    @property
    def asm(self):
        return self._asm

    @property
    def idx(self):
        o = self._offset
        return slice(o, o + self.asm.width)

    @property
    def tag_idx(self):
        o = self._offset
        return slice(o + self.asm.tag_layout[0], o + self.asm.tag_layout[1])
