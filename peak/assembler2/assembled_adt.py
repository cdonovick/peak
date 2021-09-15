import abc
from collections import Counter
from functools import reduce
import inspect
import itertools as it
import operator
import typing as tp
import traceback

from hwtypes import AbstractBitVectorMeta, TypeFamily
from hwtypes import AbstractBitVector, AbstractBit

from hwtypes.adt_meta import BoundMeta
from hwtypes.adt import Enum, Product, Sum, Tuple, TaggedUnion
from hwtypes.modifiers import is_modified

import magma as m

from .assembler_abc import AssemblerMeta
from .assembler_util import _issubclass

class _MISSING: pass

RESERVED_NAMES = frozenset({
    'adt_t',
    'assembler_t',
    'bv_type',
    'default_bv'
})

class AssembledADTMeta(BoundMeta):
    def __init__(cls, name, bases, namespace, **kwargs):
        if not cls.is_bound:
            return
        cls._assembler_ = cls.assembler_t(cls.adt_t)
        if is_modified(cls.adt_t):
            raise TypeError(f"Cannot create Assembled ADT from a modified adt type {cls.adt_t}")

    def _name_from_idx(cls, idx):
        return f'{cls.__name__}[{", ".join(map(repr, idx))}]'

    def __getitem__(cls, key: tp.Tuple[BoundMeta, AssemblerMeta, AbstractBitVectorMeta]):
        if cls.is_bound:
            val = cls.adt_t[key]
            return cls.unbound_t[(val, *cls.fields[1:])]
        else:
            adt_t = key[0]
            fam = key[2].get_family()
            # Bit of a hack but don't bother wrapping Bits/Bitvectors
            # Removes the issue of adding __operators__
            if _issubclass(adt_t, AbstractBit):
                return fam.Bit
            elif _issubclass(adt_t, AbstractBitVector):
                # There should really be a better way to check this
                adt_fam  = adt_t.get_family()
                if issubclass(adt_t, adt_fam.Signed):
                    return fam.Signed[adt_t.size]
                elif issubclass(adt_t, adt_fam.Unsigned):
                    return fam.Unsigned[adt_t.size]
                else:
                    return fam.BitVector[adt_t.size]

            T = super().__getitem__(key)
            return T

    def __getattr__(cls, attr):
        val = getattr(cls.adt_t, attr, _MISSING)
        if val is not _MISSING:
            return cls.unbound_t[(val, *cls.fields[1:])]
        else:
            raise AttributeError(f"{attr} not in {cls.adt_t}")

    def __contains__(cls, T):
        return T in cls.adt_t

    def __eq__(cls, other):
        mcs = type(cls)
        if isinstance(other, mcs):
            return super().__eq__(other)
        elif isinstance(other, BoundMeta) or isinstance(other, Enum):
            return cls.bv_type.get_family().Bit(cls.adt_t == other)
        elif isinstance(other, AbstractBitVector) and isinstance(cls.adt_t, Enum):
            assembler = cls.assembler(type(cls.adt_t))
            opcode = assembler.assemble(cls.adt, cls.bv_type)
            return opcode == other
        else:
            return NotImplemented

    def __ne__(cls, other):
        return ~(cls == other)

    def __hash__(cls):
        return super().__hash__()

    @property
    def adt_t(cls):
        return cls.fields[0]

    @property
    def assembler_t(cls):
        return cls.fields[1]

    @property
    def bv_type(cls):
        return cls.fields[2]

    # is_valid is a name I don't want to reserve
    def _is_valid_(cls, opcode: AbstractBitVector) -> AbstractBit:
        return cls._assembler_.is_valid(opcode)

    # For the bitvector protocol
    def _bitvector_t_(cls):
        return cls.bv_type[cls._assembler_.width]


class AssembledADT(metaclass=AssembledADTMeta):
    _value_: AbstractBitVector
    def __init__(self, adt):
        cls = type(self)
        assembler = cls._assembler_
        if isinstance(adt, cls):
            self._value_ =  adt._value_
        elif isinstance(adt, cls.adt_t):
            self._value_ = assembler.assemble(adt, cls.bv_type)
        elif not isinstance(adt, cls.bv_type[assembler.width]):
            raise TypeError(f'expected one of:\n\t{cls.bv_type[assembler.width]}\n\t{cls}\n\t{cls.adt_t}\nnot:\n\t{type(adt)}')
        else:
            self._value_ = adt

    def __getitem__(self, key):
        return self._get(key, operator.getitem)

    def __getattr__(self, attr):
        return self._get(attr, getattr)

    def _get(self, key, getter):
        cls = type(self)
        asm = cls._assembler_
        field = asm.extract(self._value_, key)

        if not _issubclass(cls.adt_t, Sum):
            if issubclass(getter(cls.adt_t, key), AbstractBit):
                assert field.size == 1
                return field[0]
            return field

        asm_field = getter(cls, key)(field)

        match = asm.match(self._value_, key)
        return cls.adt_t.Match(match, asm_field, safe=False)

    def __hash__(self):
        return hash(self._value_)

    def __repr__(self):
        return f'{type(self).__name__}({self._value_})'

    def __eq__(self, other):
        cls = type(self)
        if isinstance(other, cls):
            return self._value_ == other._value_
        elif isinstance(other, cls.bv_type[cls._assembler_.width]):
            return self._value_ == other
        elif isinstance(other, cls.adt_t):
            opcode = cls._assembler_.assemble(other, cls.bv_type)
            return self._value_ == opcode
        else:
            return NotImplemented

    def __ne__(cls, other):
        return ~(cls == other)

    @classmethod
    def from_fields(cls, *args, **kwargs):
        def _as_bv(v):
            if isinstance(v, AbstractBitVector):
                bv_value = v
            elif isinstance(v, AbstractBit):
                bv_value = v.get_family().BitVector[1](v)
            elif isinstance(v, AssembledADT):
                bv_value = v._value_
            elif isinstance(v, cls.adt_t):
                bv_value = cls._assembler_.assemble(v, cls.bv_type)
            else:
                raise TypeError(v, type(v))

            return bv_value

        if issubclass(cls.adt_t, Sum) and not issubclass(cls.adt_t, TaggedUnion):
            if len(args) != 2:
                raise TypeError('Expected two positional arguments')
            args = args[0], _as_bv(args[1])
        else:
            args = map(_as_bv, args)

        kwargs = {k: _as_bv(v) for k, v in kwargs.items()}
        return cls(cls._assembler_.from_fields(*args, **kwargs))

    # For the bitvector protocol
    @classmethod
    def _from_bitvector_(cls, value):
        return cls(value)

    def _to_bitvector_(self):
        return self._value_


class MAADTMeta(AssembledADTMeta, m.MagmaProtocolMeta):
    def _bases_from_idx(cls, idx):
        return super()._bases_from_idx(idx[:-1])

    def _to_magma_(cls):
        return cls._bitvector_t_().qualify(cls.fields[3])

    def _qualify_magma_(cls, d):
        return cls.unbound_t[(*cls.fields[:-1], d)]

    def _flip_magma_(cls):
        d = cls.fields[3]
        if d == m.Direction.In:
            return cls.unbound_t[(*cls.fields[:-1], m.Direction.Out)]
        elif d == m.Direction.Out:
            return cls.unbound_t[(*cls.fields[:-1], m.Direction.In)]
        else:
            return cls

    def _from_magma_value_(cls, value):
        if not value.is_oriented(cls.fields[3]):
            raise TypeError('value is not properly oriented')
        return cls._from_bitvector_(value)


class MagmaADT(AssembledADT, m.MagmaProtocol, metaclass=MAADTMeta):
    _get_magma_value_ = AssembledADT._to_bitvector_


class AssembledADTRecursor(metaclass=abc.ABCMeta):
    def __call__(self, aadt_t, *args, **kwargs):
        if (issubclass(aadt_t, AbstractBit) or issubclass(aadt_t, AbstractBitVector)):
            return self.bv(aadt_t,*args,**kwargs)
        adt_t = aadt_t.adt_t
        if issubclass(adt_t, Enum):
            return self.enum(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, TaggedUnion):
            return self.tagged_union(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Sum):
            return self.sum(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Product):
            return self.product(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Tuple):
            return self.tuple(aadt_t, *args, **kwargs)
        else:
            raise ValueError("Unreachable")

    @abc.abstractmethod
    def bv(self, aadt_t, *args, **kwargs): pass

    @abc.abstractmethod
    def enum(self, aadt_t, *args, **kwargs): pass

    @abc.abstractmethod
    def sum(self, aadt_t, *args, **kwargs): pass

    @abc.abstractmethod
    def tagged_union(self, aadt_t, *args, **kwargs): pass

    @abc.abstractmethod
    def product(self, aadt_t, *args, **kwargs): pass
