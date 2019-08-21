import typing as tp

from magma.bitutils import clog2

from hwtypes.adt import Enum, Sum, Product
from hwtypes import AbstractBit, AbstractBitVector

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
    if issubclass(type, AbstractBit):
        s = 1
    elif issubclass(type, AbstractBitVector):
        s = type.size
    elif issubclass(type, Enum):
        return clog2(len(list(type.enumerate())))
    elif issubclass(type, Product):
        s = sum([size(getattr(type,key)) for key in type.field_dict])
    elif issubclass(type, Sum):
        s = max([size(f) for f in type.fields]) + sumsize(type)
    return s

def sumsize(type):
    if issubclass(type, Sum):
        if hasattr(type, 'tags'):
            s = clog2(max([val for val in type.tags.values()])+1)
        else:
            s = clog2(len(type.fields))
    return s

def instkey(inst):
    t = type(inst)
    if hasattr(t, 'tags'):
        i = t.tags[type(inst.value)]
    else:
        i = list(t.fields).index(type(inst.value))
    return i

def bitfield(i):
    def wrap(klass):
        klass.bitfield = i
        return klass
    return wrap

def encode(inst, bitfield=0):
    bitfield = getattr(inst, 'bitfield', bitfield)
    if isinstance(inst, (AbstractBit, AbstractBitVector)):
        word = int(inst) << bitfield
    elif isinstance(inst,Enum):
        word = inst.value << bitfield
    elif isinstance(inst,Product):
        word = 0
        for key in type(inst).field_dict.keys():
            field = getattr(inst, key)
            word |= encode(field, bitfield)
            bitfield += size(type(field))
    elif isinstance(inst,Sum):
        i = instkey(inst)
        t = type(inst)
        word = (i | (encode(inst.value, sumsize(t)))) << bitfield
    else:
        raise ValueError(inst)
    return word
