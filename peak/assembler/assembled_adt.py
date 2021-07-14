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
class _TAG: pass

RESERVED_NAMES = frozenset({
    'adt_t',
    'assembler_t',
    'bv_type',
    'default_bv'
})

#Given a layout specification and field values, construct a bitvector using concatenation
def _create_from_layout(width, layout, field_bvs, bv_type: AbstractBitVector, default_value: int):
    if layout.keys() != field_bvs.keys():
        raise ValueError('layout does not match field_bvs')
    ranges = sorted(layout.values())
    if not all(
            type(r0) == type(r1) == tuple
            and len(r0) == len(r1) == 2
            # ranges are not overlapping and are bounded by (0, width)
            and 0 <= r0[0] < r0[1] <= r1[0] < r1[1] <= width
            for r0, r1 in zip(ranges, ranges[1:])):
        raise ValueError('invalid layout')

    slots = [bv_type[1](default_value) for i in range(width)]
    for field_name, (low, hi) in layout.items():
        # need to add None to keep the indexing consistent
        slots[low:hi] = field_bvs[field_name], *(None for _ in range(low+1, hi))
    bv = reduce(bv_type.concat, (_as_bv(s) for s in slots if s is not None))
    assert bv.size == width
    #Need to cast to bv_type since magma's concats do not return bv_type
    return bv_type[width](bv)


def _as_bv(v):
    if isinstance(v, AbstractBitVector):
        bv_value = v
    elif isinstance(v, AbstractBit):
        bv_value = v.get_family().BitVector[1](v)
    elif isinstance(v, AssembledADT):
        bv_value = v._value_
    else:
        raise TypeError(type(v))

    return bv_value


def _taggedunion_from_fields(cls, *, tag_bv=None, default_bv=0, **kwargs):
    if len(kwargs) != 1:
        raise  TypeError('Expected exactly one keyword argument')

    tag, value = kwargs.popitem()
    value_bv = getattr(cls, tag)(value)
    return _sum_or_tagged_from_fields(cls, tag, tag_bv, value_bv, default_bv)



def _sum_from_fields(cls, tag, value,  *,
        tag_bv=None, default_bv=0):

    value_bv = cls[tag](value)
    return _sum_or_tagged_from_fields(cls, tag, tag_bv, value_bv, default_bv)


def _sum_or_tagged_from_fields(cls, tag, tag_bv, value_bv, default_bv):
    assembler = cls._assembler_

    if tag_bv is None:
        tag_bv = assembler.assemble_tag(tag, cls.bv_type)

    fields = {
        'value': value_bv,
        'tag': tag_bv,
    }

    layout = {
        'value': assembler.layout[tag],
        'tag': assembler.tag_layout,
    }

    bv_value = _create_from_layout(
            assembler.width, layout, fields, cls.bv_type, default_bv)
    return cls(bv_value)



def _product_from_fields(cls, *args, default_bv=0, **kwargs):
    sig = inspect.signature(cls.adt_t.__init__)
    # ... for self
    bound = sig.bind(..., *args, **kwargs)
    fields = bound.arguments
    fields = {k: getattr(cls, k)(v) for k, v in fields.items() if k != 'self'}
    assembler = cls._assembler_
    bv_value = _create_from_layout(
            assembler.width, assembler.layout, fields, cls.bv_type, default_bv)
    return cls(bv_value)


def _tuple_from_fields(cls, *args, default_bv=0):
    if len(args) != len(cls.adt_t.fields):
        raise  TypeError('Incorrect number of positional arguments')

    assembler = cls._assembler_
    fields = {i: cls[i](v) for i, v in enumerate(args)}
    bv_value = _create_from_layout(
            assembler.width, assembler.layout, fields, cls.bv_type, default_bv)
    return cls(bv_value)

def _enum_from_fields(cls, value, *, default_bv=0):
    return cls(value)

class AssembledADTMeta(BoundMeta):
    def __init__(cls, name, bases, namespace, **kwargs):
        if not cls.is_bound:
            return
        cls._assembler_ = cls.assembler_t(cls.adt_t)
        if is_modified(cls.adt_t):
            raise TypeError(f"Cannot create Assembled ADT from a modified adt type {cls.adt_t}")
        if issubclass(cls.adt_t, Product):
            cls.from_fields = classmethod(_product_from_fields)
        elif issubclass(cls.adt_t, Tuple):
            cls.from_fields = classmethod(_tuple_from_fields)
        elif issubclass(cls.adt_t, Enum):
            cls.from_fields = classmethod(_enum_from_fields)
        elif issubclass(cls.adt_t, TaggedUnion):
            cls.from_fields = classmethod(_taggedunion_from_fields)
        elif issubclass(cls.adt_t, Sum):
            cls.from_fields = classmethod(_sum_from_fields)
        else:
            return

    def __call__(cls, *args, **kwargs):
        # Dirty hack to make it seem like init can be called like from_fields
        # In the face ambiguity it will use old constructor
        if issubclass(cls.adt_t, Enum):
            # Avoid infinite recusion in enums on error cases
            # as from_fields just calls __call__
            return super().__call__(*args, **kwargs)
        else:
            try:
                return super().__call__(*args, **kwargs)
            except TypeError:
                return cls.from_fields(*args, **kwargs)

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
        return self._get(key, operator.getitem, KeyError)

    def __getattr__(self, attr):
        return self._get(attr, getattr, AttributeError)

    def _get(self, key, getter, Error):
        cls = type(self)
        sub = cls._assembler_.sub.get(key, _MISSING)
        if sub is not _MISSING:
            if issubclass(getter(cls, key), AbstractBit):
                field = self._value_[sub.idx][0]
            else:
                field = getter(cls, key)(self._value_[sub.idx])
        elif key is _TAG and not _issubclass(cls.adt_t, Sum):
            raise Error(f"can only get tag from Sum types")
        elif not key is _TAG:
            raise Error(f"{key} not in {list(cls.adt_t.field_dict.items())}")

        if not _issubclass(cls.adt_t, Sum):
            return field

        tag = self._value_[cls._assembler_.sub.tag_idx]

        if key is _TAG:
            return tag

        # if key is an assembled adt class just grab the type from it
        if _issubclass(key, cls.unbound_t):
            T = key.adt_t
        else:
            T = key

        if T in cls.adt_t.field_dict:
            T = cls._assembler_.assemble_tag(T, cls.bv_type)

        if not isinstance(T, cls.bv_type[cls._assembler_.tag_width]):
            raise TypeError(type(T), T, cls.adt_t)

        match = tag == T
        return cls.adt_t.Match(match, field, safe=False)


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
