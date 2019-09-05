import typing as tp
from .assembler_abc import AssemblerMeta
from hwtypes import AbstractBitVectorMeta, TypeFamily, Enum, Sum, Product, Tuple
from hwtypes import AbstractBitVector, AbstractBit
from hwtypes.adt_meta import BoundMeta

from uuid import uuid1

from .assembler_util import _issubclass

class _MISSING: pass


RESERVED_NAMES = frozenset({
    'adt_t',
    'assembler_t',
    'bv_type',
    'from_subfields'
})

#Given a layout specification and subfield values, construct a bitvector using concatenation
def _create_from_layout(width, bv_vals, layout, default_bv : AbstractBitVector[1]):

    #Check the layout is mutually exclusive
    used_slots = [0 for _ in range(width)]
    for (lo, hi) in layout.values():
        for i in range(lo, hi):
            used_slots[i] +=1
    assert all(x < 2 for x in used_slots)

    #Pad all the empty slots with default_bv
    for i in range(width):
        if used_slots[i] == 0:
            k = uuid1()
            layout[k] = (i, i+1)
            bv_vals[k] = default_bv

    def _get_lo(kv):
        lo, hi = kv[1]
        return lo
    #I need to organize values by layout order.
    sorted_layout = sorted(layout.items(), key=_get_lo)

    #make sure augemnted layout is packed tightly
    idx = 0
    for v in sorted_layout:
        lo, hi = v[1]
        assert idx == lo
        idx = hi
    assert idx == width

    val = bv_vals[sorted_layout[0][0]]
    for name, _ in sorted_layout[1:]:
        val = val.concat(bv_vals[name])

    assert val.size == width
    return val

#method that returns the bitvector of a subfield
def _field_to_bv(aadt_t, v):
    if (_issubclass(aadt_t, AbstractBitVector)
        or _issubclass(aadt_t, AbstractBit)):
        bv_t = aadt_t.get_family().BitVector
        if not isinstance(v, aadt_t):
            raise TypeError(f'expected {aadt_t}, not {v}')
        if _issubclass(aadt_t, AbstractBitVector):
            bv_value = v
        else:
            bv_value = v.ite(bv_t[1](1), bv_t[1](0))
    else:
        bv_t = aadt_t.bv_type
        sub_assembler = aadt_t.assembler_t(aadt_t.adt_t)
        if isinstance(v, aadt_t):
            bv_value = v._value_
        elif isinstance(v, aadt_t.adt_t):
            bv_value = sub_assembler.assemble(v, bv_t)
        elif isinstance(v, bv_t[sub_assembler.width]):
            bv_value = v
        else:
            raise TypeError(f'expected {aadt_t} or {aadt_t.adt_t} or {bv_t[sub_assembler.width]} but not {v}')
    return bv_value

def _create_from_product(assembled_adt):
    adt_t, assembler_t, bv_t = assembled_adt.fields
    assembler = assembler_t(adt_t)
    #kwargs should be correctly passed by names
    def _product(**kwargs):
        bv_values = {}
        for k, v in kwargs.items():
            aadt_t = getattr(assembled_adt, k)
            bv_values[k] = _field_to_bv(aadt_t, v)
        bv_value = _create_from_layout(assembler.width, bv_values, assembler.layout, default_bv=bv_t[1](0) )
        return assembled_adt(bv_value)
    return _product

def _create_from_tuple(assembled_adt):
    adt_t, assembler_t, bv_t = assembled_adt.fields
    assembler = assembler_t(adt_t)
    #kwargs should be correctly passed by names
    def _tuple(*args):
        bv_values = {}
        for idx, v in enumerate(args):
            aadt_t = assembled_adt[idx]
            bv_values[idx] = _field_to_bv(aadt_t, v)
        bv_value = _create_from_layout(assembler.width, bv_values, assembler.layout, default_bv=bv_t[1](0))
        return assembled_adt(bv_value)
    return _tuple

class _TAG: pass

def _create_from_sum(assembled_adt):
    adt_t, assembler_t, bv_t = assembled_adt.fields
    assembler = assembler_t(adt_t)

    def _sum(value):
        #I need to figure out how to pass this value into _field_to_bv
        bv_values = []
        for name, field in adt_t.field_dict.items():
            aadt_t = assembled_adt[field]
            try:
                bv_value = _field_to_bv(aadt_t, value)
                bv_values.append((name, field, bv_value))
            except TypeError:
                pass
        #Only one of the Sum types should match
        if len(bv_values) == 0:
            raise TypeError(f'{value} not valid for sum type {assembled_adt}')
        elif len(bv_values) > 1:
            raise TypeError(f'{value} is ambiguous for sum type {assembled_adt}')

        #Construct the layout of the Tag and the one field
        name, field, bv_value  = bv_values[0]
        layout = {_TAG: assembler._tag_layout, field: assembler.layout[field]}
        tag_val = assembler._tag_asm(field)
        tag_bv = bv_t[assembler._tag_width](tag_val)
        bv_values = {_TAG: tag_bv, field: bv_value}
        bv_value = _create_from_layout(assembler.width, bv_values, layout, default_bv=bv_t[1](0))
        return assembled_adt(bv_value)
    return _sum

class AssembledADTMeta(BoundMeta):

    def __init__(cls, name, bases, namespace, **kwargs):
        if not cls.is_bound:
            return
        if issubclass(cls.adt_t, Product):
            type_sig = ', '.join(f'{k}: {v.__name__!r}' for k, v in cls.adt_t.field_dict.items())
            # build from_subfields
            _product = _create_from_product(cls)
            _call_product = ', '.join(f'{k}={k}' for k in cls.adt_t.field_dict)
            from_subfields = f'''
def from_subfields({type_sig}):
    return _product({_call_product})
'''
            gs = dict(
                _product=_product
            )
            ls = {}
            exec(from_subfields, gs, ls)
            cls.from_subfields = ls['from_subfields']
        elif issubclass(cls.adt_t, Tuple):
            type_sig = ", ".join(f'_{k}: {v.__name__!r}' for k, v in cls.adt_t.field_dict.items())
            _tuple = _create_from_tuple(cls)
            _call_tuple = ', '.join(f'_{k}' for k in cls.adt_t.field_dict)
            from_subfields = f'''
def from_subfields({type_sig}):
    return _tuple({_call_tuple})
'''
            gs = dict(
                _tuple=_tuple
            )
            ls = {}
            exec(from_subfields, gs, ls)
            cls.from_subfields = ls['from_subfields']
        elif issubclass(cls.adt_t, Sum):
            cls.from_subfields = _create_from_sum(cls)

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
            #This looks sketchy. Does it work for SMT?
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
            raise TypeError(type(T), T, cls.adt_t)

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
