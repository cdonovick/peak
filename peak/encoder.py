from .adt import Enum, ISABuilder, Product, Sum, Tuple
from collections import OrderedDict
from functools import reduce
from hwtypes import AbstractBitVector,BitVector
import operator

def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False


def get_width(isa : ISABuilder):
    if _issubclass(isa, Enum):
        return max(i.value for i in isa).bit_length()
    elif _issubclass(isa, (Tuple, Product)):
        return sum(map(get_width, isa.fields))
    elif _issubclass(isa, Sum):
        return  max(map(get_width, isa.fields)) + len(isa.fields).bit_length()
    elif _issubclass(isa, AbstractBitVector):
        return isa.size
    elif isinstance(isa, AbstractBitVector):
        return isa.size
    elif isinstance(isa, int):
        return BitVector(isa).size
    else:
        raise TypeError(isa)




def _enum(isa : Enum):
    encoding = {}
    decoding = {}
    layout = {}
    w = get_width(isa)
    for inst in isa:
        layout[inst] = (0, w, None)
        opcode = BitVector[w](inst.value)
        encoding[inst] = opcode
        decoding[opcode]  = inst

    def encode(inst):
        return encoding[inst]
    def decode(bv):
        return decoding[bv]

    return encode, decode, w, layout

def _product(isa : Product):
    encoding = dict()
    decoding = dict()
    layout = dict()

    width = get_width(isa)

    base = 0
    for name,field in isa._fields_dict.items():
        e, d, w, l = generate_encoder_decoder(field)
        encoding[name] = e
        decoding[name] = d
        layout[name] = (base, base+w, l)
        base += w

    assert base == width

    def encode(inst):
        opcode = BitVector[width](0)
        for name,v in inst._as_dict().items():
            v = BitVector[width](encoding[name](v))
            opcode |= v << layout[name][0]
        return opcode

    def decode(opcode):
        args = []
        for name,d in decoding.items():
            base, top, _ = layout[name]
            args.append(d(opcode[base:top]))
        return isa(*args)

    return encode, decode, width, layout

def _sum(isa : Sum):
    encoding = {}
    decoding = {}
    layout = {}
    width = get_width(isa)
    tag_width = len(isa.fields).bit_length()

    for tag, field in enumerate(isa.fields):
        tag = BitVector[tag_width](tag)
        e, d, w, l = generate_encoder_decoder(field)
        assert tag_width + w <= width
        encoding[field] = tag, e,
        decoding[tag] = d, w
        layout[field] = (tag_width, tag_width+w, l)

    def encode(inst):
        opcode = BitVector[width](0)
        field = type(inst.value)
        tag, e = encoding[field]
        assert tag.size == tag_width, (tag, tag.size, tag_width)
        tag = tag.zext(width - tag_width)
        pay_load = e(inst.value)
        pay_load = pay_load.zext(width - pay_load.size)
        opcode |= tag
        opcode |= pay_load << tag_width
        return opcode

    def decode(opcode):
        tag = opcode[0:tag_width]
        d, w = decoding[tag]
        return isa(d(opcode[tag_width:tag_width + w]))

    return encode, decode, width, layout

def _bv(isa : AbstractBitVector):
    def encode(inst):
        return inst
    def decode(opcode):
        return isa(opcode)
    return encode, decode, get_width(isa), None


def generate_encoder_decoder(isa : ISABuilder):
    if _issubclass(isa, Enum):
        return _enum(isa)
    elif _issubclass(isa, Product):
        return _product(isa)
    elif _issubclass(isa, Sum):
        return _sum(isa)
    elif _issubclass(isa, AbstractBitVector):
        return _bv(isa)
    elif isinstance(isa, AbstractBitVector):
        return _bv(isa)
    elif isinstance(isa, int):
        return _bv(BitVector(isa))
    else:
        raise TypeError()

