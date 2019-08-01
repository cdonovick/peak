import typing as tp
from .assembler_abc import AssemblerMeta
from hwtypes import AbstractBitVectorMeta, TypeFamily, Enum
from hwtypes.adt_meta import BoundMeta

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
            for name in RESERVED_NAMES:
                if hasattr(adt_t, name):
                    raise TypeError()
            return super().__getitem__(key)

    def __getattr__(cls, attr):
        val = getattr(cls.adt_t, attr, _MISSING)
        if val is not _MISSING:
            return cls.unbound_t[val, cls.assembler_t, cls.bv_type]
        else:
            raise AttributeError(attr)

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
        elif not isinstance(adt, cls.bv_type):
            raise TypeError()
        else:
            self._value_ = adt

    def __getitem__(self, key):
        cls = type(self)
        asm = self._assembler_.sub.get(key, _MISSING)
        if asm is not _MISSING:
            return cls[key](self._value_[asm.idx])
        else:
            raise KeyError(key)

    def __getattr__(self, attr):
        cls = type(self)
        asm = self._assembler_.sub.get(attr, _MISSING)
        if asm is not _MISSING:
            return getattr(cls, attr)(self._value_[asm.idx])
        else:
            raise AttributeError(attr)

    def __eq__(self, other):
        cls = type(self)
        if isinstance(other, cls):
            return self._value_ == other._value_
        elif isinstance(other, cls.bv_type):
            return self._value_ == other
        elif isinstance(other, cls.adt_t):
            opcode = self._assembler_.assemble(other, cls.bv_type)
            return self._value_ == opcode
        else:
            return NotImplemented

    def __ne__(self, other):
        return ~(self == other)

    def __hash__(self):
        return hash(self._value_)

    def __repr__(self):
        return f'{type(self).__name__}({self._value_})'
