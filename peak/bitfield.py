import typing as tp

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


def bitfield(i):
    def wrap(klass):
        klass.bitfield = i
        return klass
    return wrap

def encode(inst, bitfield=0):
    #print(inst, type(inst))

    if hasattr(inst, 'bitfield'):
        bitfield = inst.bitfield

    if isinstance(inst, (AbstractBit, AbstractBitVector)):
        word = int(inst) << bitfield
    elif isinstance(inst,Enum):
        word = inst.value << bitfield
    elif isinstance(inst,Product):
        word = 0
        for key in type(inst).field_dict.keys():
            field = getattr(inst, key)
            if hasattr(field, 'bitfield'):
                word |= encode(field)
            else:
                word |= encode(field) << bitfield
                if isinstance(field, AbstractBit):
                    bitfield += 1
                elif isinstance(field, AbstractBitVector):
                    bitfield += field.size
    elif isinstance(inst,Sum):
        t = type(inst)
        if hasattr(t, 'tags'):
            i = t.tags[type(inst.value)]
        else:
            i = list(t.fields).index(type(inst.value))
        word = (i << bitfield) | encode(inst.value)
    else:
        raise ValueError(inst)
    return word
