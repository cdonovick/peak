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

# left vs right justify
def encode(inst, reverse=False):
    bitfield = getattr(inst, 'bitfield', 0)
    if isinstance(inst, (AbstractBit, AbstractBitVector, Enum)):
        # depreciated
        word = inst._value_ if isinstance(inst,Enum) else int(inst)
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
                # depreciated
                word = (tag << pos) | encode(inst._value_, reverse)
            else: # tag is on the right, value is on the left
                pos = sumsize(typeinst)
                word = (encode(inst._value_) << pos) | tag
        else:
            raise ValueError(inst)
    return word << bitfield

