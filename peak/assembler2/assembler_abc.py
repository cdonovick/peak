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
    @abstractmethod
    def width(self) -> int:
        pass

    @abstractmethod
    def assemble(self, inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        pass

    @abstractmethod
    def disassemble(self, bv: BitVector) -> 'Type[self._isa]':
        pass

    @abstractmethod
    def extract(self, bv: AbstractBitVector, field: tp.Union[str, int, type]) -> AbstractBitVector:
        pass

    @abstractmethod
    def match(self, bv: AbstractBitVector, field: tp.Union[str, type]) -> AbstractBit:
        pass

    @abstractmethod
    def is_valid(self, opcode: AbstractBitVector) -> AbstractBit:
        pass

    @abstractmethod
    def from_fields(self, *args, **kwargs) -> AbstractBitVector:
        pass
