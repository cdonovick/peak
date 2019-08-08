import typing as tp
from .assembler_abc import AssemblerMeta
from hwtypes import AbstractBitVectorMeta, TypeFamily, Enum, Sum
from hwtypes import AbstractBitVector, AbstractBit
from hwtypes.adt_meta import BoundMeta

from .assembler_util import _issubclass

class _MISSING: pass


RESERVED_NAMES = frozenset({
    'adt_t',
    'assembler_t',
    'bv_type',
})


class AssembledADTMeta(BoundMeta):
    def _name_cb(cls, idx):
        return f'{cls.__name__}[{", ".join(map(repr, idx))}]'

    def __getitem__(cls, key: tp.Tuple[BoundMeta, AssemblerMeta, AbstractBitVectorMeta]):
        if cls.is_bound:
            val = cls.adt_t[key]
            return cls.unbound_t[val, cls.assembler_t, cls.bv_type]
        elif len(key) != 3:
            raise TypeError('AssembledADTs must be bound to a BoundMeta, AssemblerMeta, BitVector')
        else:
            adt_t = key[0]
            if (_issubclass(adt_t, AbstractBitVector)
                or _issubclass(adt_t, AbstractBit)):
                # Bit of a hack but don't bother wrapping Bits/Bitvectors
                # Removes the issue of adding __operators__
                return adt_t
            for name in RESERVED_NAMES:
                if hasattr(adt_t, name):
                    raise TypeError()
            T = super().__getitem__(key)
            return T

    def __getattr__(cls, attr):
        val = getattr(cls.adt_t, attr, _MISSING)
        if val is not _MISSING:
            return cls.unbound_t[val, cls.assembler_t, cls.bv_type]
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

        if isinstance(adt, cls.adt_t):
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
                return self._value_[sub.idx][0]
            else:
                return cls[key](self._value_[sub.idx])
        else:
            raise KeyError(key)

    def __getattr__(self, attr):
        return self[attr]

    def match(self, T):
        cls = type(self)
        if not _issubclass(cls.adt_t, Sum):
            return super().match(T)
        tag = self._value_[self._assembler_.sub.tag_idx]
        # if T is an assembled adt class just grab the type from it
        if _issubclass(T, AssembledADT):
            T = T.adt_t

        if isinstance(T, cls.bv_type[self._assembler_.tag_width]):
            return tag == T
        elif T in cls.adt_t:
            T = self._assembler_.assemble_tag(T, cls.bv_type)
            return tag == T
        else:
            raise TypeError()

    def __hash__(self):
        return hash(self._value_)

    def __repr__(self):
        return f'{type(self).__name__}({self._value_})'

    def __eq__(self, other):
        cls = type(self)
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
