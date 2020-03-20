import abc
from collections import Counter
from functools import reduce
import itertools as it
import typing as tp

from hwtypes import AbstractBitVectorMeta, TypeFamily, Enum, Sum, Product, Tuple
from hwtypes import AbstractBitVector, AbstractBit
from hwtypes.adt_meta import BoundMeta
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
def _create_from_layout(width, layout, field_bvs, default_bv : AbstractBitVector[1]):
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

    slots = [default_bv for i in range(width)]
    for field_name, (low, hi) in layout.items():
        # need to add None to keep the indexing consistent
        slots[low:hi] = field_bvs[field_name], *(None for _ in range(low+1, hi))
    bv = reduce(type(default_bv).concat, (s for s in slots if s is not None))
    assert bv.size == width
    return bv


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


def _tuple_builder(cls, *args, default_bv):
    adt_t = cls.adt_t
    assert len(args) == len(adt_t.fields)

    assembler = cls.assembler_t(adt_t)
    fields = {i: _as_bv(cls[i](v)) for i, v in enumerate(args)}
    bv_value = _create_from_layout(
            assembler.width, assembler.layout, fields, default_bv)
    return cls(bv_value)


def _product_builder(cls, *, default_bv, **kwargs):
    adt_t = cls.adt_t
    assert kwargs.keys() == adt_t.field_dict.keys()
    assembler = cls.assembler_t(adt_t)

    fields = {k: _as_bv(getattr(cls, k)(v)) for k, v in kwargs.items()}
    bv_value = _create_from_layout(
            assembler.width, assembler.layout, fields, default_bv)
    return cls(bv_value)


def _sum_builder(cls, T, value, *, tag_bv, default_bv):
    adt_t = cls.adt_t
    assembler = cls.assembler_t(adt_t)
    if tag_bv is not None:
        assert isinstance(tag_bv, cls.bv_type)
        assert tag_bv.size == assembler.tag_width
    else:
        tag_bv = assembler.assemble_tag(T, cls.bv_type)

    fields = {
        'value': _as_bv(cls[T](value)),
        'tag': tag_bv,
    }
    layout = {
        'value': assembler.layout[T],
        'tag': assembler.tag_layout,
    }

    bv_value = _create_from_layout(
            assembler.width, layout, fields, default_bv)
    return cls(bv_value)


class AssembledADTMeta(BoundMeta):
    def __init__(cls, name, bases, namespace, **kwargs):
        if not cls.is_bound:
            return
        assembler = cls.assembler_t(cls.adt_t)
        default_bv_arg = (
            f'default_bv',
            f'tp.Optional[{cls.bv_type.__name__!r}[1]] = None',
        )
        if is_modified(cls.adt_t):
            raise TypeError(f"Cannot create Assembled ADT from a modified adt type {cls.adt_t}")
        if issubclass(cls.adt_t, Product):
            arg_strs = [(f'{k}', f'{v.__name__!r}')
                    for k, v in cls.adt_t.field_dict.items()]
            sig_args = it.chain(arg_strs, [('*',), default_bv_arg])
            sig = ', '.join(map(': '.join, sig_args))
            builder_args = ', '.join(it.starmap('{0}={0}'.format, arg_strs))
            builder = _product_builder
        elif issubclass(cls.adt_t, Tuple):
            arg_strs = [(f'_{k}', f'{v.__name__!r}')
                    for k, v in cls.adt_t.field_dict.items()]
            sig_args = it.chain(arg_strs, [('*',), default_bv_arg])
            sig = ', '.join(map(': '.join, sig_args))
            builder_args = ', '.join(k[0] for k in arg_strs)
            builder = _tuple_builder
        elif issubclass(cls.adt_t, Sum):
            value_types = ', '.join(
                map(
                    lambda t: repr(t.__name__),
                    (cls.bv_type, *cls.adt_t.fields)
                )
            )
            tag_type = f'{cls.bv_type.__name__!r}[{assembler.tag_width}]'
            sig = (
                f'T: type, '
                f'value: tp.Union[{value_types}], '
                f'*, '
                f'tag_bv: tp.Optional[{tag_type}] = None, '
                f'{default_bv_arg[0]}: {default_bv_arg[1]}'
            )
            builder_args = ('T=T, value=value, tag_bv=tag_bv')
            builder = _sum_builder
        else:
            return

        from_fields = f'''
@classmethod
def from_fields(cls, {sig}) -> {cls.__name__!r}:
    if default_bv is None:
        default_bv = cls.bv_type[1](0)

    return builder(cls, {builder_args}, default_bv=default_bv)
'''
        env = dict(builder=builder, tp=tp)
        exec(from_fields, env, env)
        cls.from_fields = env['from_fields']

    def _name_from_idx(cls, idx):
        return f'{cls.__name__}[{", ".join(map(repr, idx))}]'

    def __getitem__(cls, key: tp.Tuple[BoundMeta, AssemblerMeta, AbstractBitVectorMeta]):
        if cls.is_bound:
            val = cls.adt_t[key]
            return cls.unbound_t[(val, *cls.fields[1:])]
        else:
            adt_t = key[0]
            if (_issubclass(adt_t, AbstractBitVector)
                or _issubclass(adt_t, AbstractBit)):
                # Bit of a hack but don't bother wrapping Bits/Bitvectors
                # Removes the issue of adding __operators__
                return adt_t
            T = super().__getitem__(key)
            return T

    def __getattr__(cls, attr):
        val = getattr(cls.adt_t, attr, _MISSING)
        if val is not _MISSING:
            return cls.unbound_t[(val, *cls.fields[1:])]
        else:
            raise AttributeError(attr)

    def __contains__(cls, T):
        return T in cls.adt_t

    def __eq__(cls, other):
        mcs = type(cls)
        if isinstance(other, mcs):
            return super().__eq__(other)
        elif isinstance(other, BoundMeta) or isinstance(other, Enum):
            return cls.bv_type.get_family().Bit(cls.adt_t == other)
        elif isinstance(other, BitVector) and isinstance(cls.adt_t, Enum):
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


class AssembledADT(metaclass=AssembledADTMeta):
    def __init__(self, adt):
        cls = type(self)
        self._assembler_ = assembler = cls.assembler_t(cls.adt_t)

        if isinstance(adt, cls):
            self._value_ =  adt._value_
        elif isinstance(adt, cls.adt_t):
            self._value_ = assembler.assemble(adt, cls.bv_type)
        elif not isinstance(adt, cls.bv_type[assembler.width]):
            raise TypeError(f'expected {cls.bv_type[assembler.width]} or {cls.adt_t} not {adt}')
        else:
            self._value_ = adt

    def __getitem__(self, key):
        cls = type(self)
        sub = self._assembler_.sub.get(key, _MISSING)
        if sub is not _MISSING:
            if issubclass(cls[key], AbstractBit):
                field = self._value_[sub.idx][0]
            else:
                field = cls[key](self._value_[sub.idx])
        elif key is _TAG and not _issubclass(cls.adt_t, Sum):
            raise KeyError(f"can only get tag from Sum types")
        elif not key is _TAG:
            raise KeyError(key)

        if not _issubclass(cls.adt_t, Sum):
            return field
        tag = self._value_[self._assembler_.sub.tag_idx]
        # if key is an assembled adt class just grab the type from it
        if key is _TAG:
            return tag

        if _issubclass(key, AssembledADT):
            T = key.adt_t
        else:
            T = key

        if T in cls.adt_t:
            T = self._assembler_.assemble_tag(T, cls.bv_type)
        if not isinstance(T, cls.bv_type[self._assembler_.tag_width]):
            raise TypeError(type(T), T, cls.adt_t)
        match = tag == T
        return cls.adt_t.Match(match, field, safe=False)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            pass
        raise AttributeError(attr)

    def __hash__(self):
        return hash(self._value_)

    def __repr__(self):
        return f'{type(self).__name__}({self._value_})'

    def __eq__(self, other):
        cls = type(self)
        #The bug is here. cls.adt_t (opcode) is different than opcode
        if isinstance(other, cls):
            return self._value_ == other._value_
        elif isinstance(other, cls.bv_type[self._assembler_.width]):
            return self._value_ == other
        elif isinstance(other, cls.adt_t):
            opcode = self._assembler_.assemble(other, cls.bv_type)
            return self._value_ == opcode
        else:
            return NotImplemented

    def __ne__(cls, other):
        return ~(cls == other)

class AssembledADTRecursor:
    def __call__(self, aadt_t, *args, **kwargs):
        if (issubclass(aadt_t, AbstractBit) or issubclass(aadt_t, AbstractBitVector)):
            return self.bv(aadt_t,*args,**kwargs)
        adt_t = aadt_t.adt_t
        if issubclass(adt_t, Enum):
            return self.enum(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Sum):
            return self.sum(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Product):
            return self.product(aadt_t, *args, **kwargs)
        elif issubclass(adt_t, Tuple):
            return self.tuple(aadt_t, *args, **kwargs)
        else:
            raise ValueError("Unreachable")

    @abc.abstractmethod
    def bv(self):
        return

    @abc.abstractmethod
    def enum(self):
        return

    @abc.abstractmethod
    def sum(self):
        return

    @abc.abstractmethod
    def product(self):
        return

class MAADTMeta(AssembledADTMeta, m.MagmaProtocolMeta):
    def _bases_from_idx(cls, idx):
        return super()._bases_from_idx(idx[:-1])

    def _to_magma_(cls):
        assembler = cls.assembler_t(cls.adt_t)
        return cls.bv_type[assembler.width].qualify(cls.fields[3])

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
        return cls(value)


class MagmaADT(AssembledADT, m.MagmaProtocol, metaclass=MAADTMeta):
    def _get_magma_value_(self):
        return self._value_
