from hwtypes.adt import Enum, Sum, Product
from hwtypes import AbstractBitVector

def bitfield(i):
    def wrap(klass):
        klass.bitfield = i
        return klass
    return wrap

def encode(inst, *args):
    #print(inst, type(inst))
    if isinstance(inst, AbstractBitVector):
        word = int(inst) << inst.bitfield
    elif isinstance(inst,Enum):
        word = inst._value_ << inst.bitfield
    elif isinstance(inst,Product):
        word = 0
        for key in type(inst).field_dict.keys():
            word |= encode(getattr(inst, key))
    elif isinstance(inst,Sum):
        t = type(inst)
        i = list(t.fields).index(type(inst._value_))
        word = (i << t.bitfield) | encode(inst._value_)
    else:
        raise ValueError(inst)
    return word
