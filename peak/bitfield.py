from .bits import BV
from .enum import Enum
from .sum import Sum
from .product import Product

def bitfield(i):
    def wrap(klass):
        klass.bitfield = i
        return klass
    return wrap

def encode(inst, *args):
    #print(inst, type(inst))
    if isinstance(inst,BV):
        word = int(inst) << inst.bitfield
    elif isinstance(inst,Enum):
        word = inst.value << inst.bitfield
    elif isinstance(inst,Product):
        word = 0
        for key in inst.__annotations__.keys():
            word |= encode(getattr(inst, key))
    elif isinstance(inst,Sum):
        t = type(inst)
        i = list(t.fields).index(type(inst.a))
        word = (i << t.bitfield) | encode(inst.a)
    else:
        raise ValueError(inst)
    return word
