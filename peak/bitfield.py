import typing as tp

from magma.bitutils import clog2

from hwtypes.adt_meta import EnumMeta
from hwtypes.adt import Enum, Sum, Product
from hwtypes import AbstractBit, AbstractBitVector
from .assembler.assembler_util import _issubclass

def tag(tags: tp.Mapping[type, int]):
    def wrapper(sum: Sum):
        if not issubclass(sum, Sum):
            raise TypeError('tag can only be applied Sum')
        if tags.keys() != sum.fields:
            raise ValueError('tag must specificy an Option for each Sum option')
        if not all(isinstance(t, int) for t in tags.values()):
            raise TypeError('tags must be int')

        setattr(sum, 'tags', tags)
        return sum
    return wrapper

def size(type):
    s = 0
    if _issubclass(type, AbstractBit):
        s = 1
    elif _issubclass(type, AbstractBitVector):
        s = type.size
    elif _issubclass(type, Enum):
        return clog2(len(list(type.enumerate())))
    elif _issubclass(type, Product):
        s = sum([size(getattr(type,key)) for key in type.field_dict])
    elif _issubclass(type, Sum):
        s = max([size(f) for f in type.fields]) + sumsize(type)
    return s

def sumsize(type):
    if _issubclass(type, Sum) or _issubclass(type, Enum):
        if hasattr(type, 'tags'):
            s = clog2(max([val for val in type.tags.values()])+1)
        else:
            s = clog2(len(type.fields))
    return s

def instkey(inst):
    t = type(inst)
    if hasattr(t, 'tags'):
        # depreciated
        i = t.tags[type(inst._value_)]
    else:
        i = list(t.fields).index(type(inst._value_))
    return i

def bitfield(i):
    def wrap(klass):
        klass.bitfield = i
        return klass
    return wrap

def _enum(isa: tp.Type[Enum]) -> tp.Dict[Enum, int]:
    asm: tp.Dict[Enum, int] = {}

    free  = []
    used = set()

    for inst in isa.enumerate():
        val = inst._value_
        if isinstance(val, int):
            if (val < 0):
                raise ValueError('Enum values must be > 0')
            asm[inst] = val
            used.add(val)
        else:
            assert isinstance(val, EnumMeta.Auto)
            free.append(inst)

    c = 0
    for i in free:
        while c in used:
            c += 1
        used.add(c)
        asm[i] = c
    
    if not asm:
        raise TypeError('Enum must not be empty')

    return asm

# left vs right justify
def encode(inst, reverse=False):
    bitfield = getattr(inst, 'bitfield', 0)
    if isinstance(inst, (AbstractBit, AbstractBitVector)):
        word = int(inst)
    else:
        typeinst = type(inst)
        if isinstance(inst,Product):
            word = 0
            if reverse: # layout fields from right to left
                pos = size(typeinst)
                for key in typeinst.field_dict.keys():
                    field = getattr(inst, key)
                    len = size(type(field))
                    word |= encode(field, reverse) << (pos - len)
                    pos -= len
            else: # layout fields from left to right
                pos = 0
                for key in typeinst.field_dict.keys():
                    field = getattr(inst, key)
                    len = size(type(field))
                    word |= encode(field, reverse) << pos
                    pos += len
        elif isinstance(inst,Sum):
            tag = instkey(inst)
            if reverse: # tag is on the left, value is on the right
                pos = size(typeinst) - sumsize(typeinst)
                # depreciated - need to do a match
                word = (tag << pos) | encode(inst.value, reverse)
            else: # tag is on the right, value is on the left
                pos = sumsize(typeinst)
                word = (encode(inst.value) << pos) | tag
        elif isinstance(inst,Enum):
            # cache this ...
            values = _enum(typeinst)
            word = values[inst]
        else:
            raise ValueError(inst)
    return word << bitfield

