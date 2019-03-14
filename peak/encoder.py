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


def generate_encoder_decoder_stupid(isa : ISABuilder):
    w = len(list(isa.enumerate()))
    encoding = {}
    decoding = {}
    for idx, inst in enumerate(isa.enumerate()):
        idx = BitVector[w](idx)
        encoding[inst] = idx
        decoding[idx]  = inst


    def encode(inst):
        return encoding[inst]
    def decode(bv):
        return decoding[bv]

    return encode, decode, w


def _enum(isa : Enum):
    encoding = {}
    decoding = {}
    w = get_width(isa)
    for inst in isa:
        opcode = BitVector[w](inst.value)
        encoding[inst] = opcode
        decoding[opcode]  = inst

    def encode(inst):
        return encoding[inst]
    def decode(bv):
        return decoding[bv]

    return encode, decode, w

def _product(isa : Product):
    encoding = OrderedDict()
    decoding = OrderedDict()
    fields_range = OrderedDict()

    width = get_width(isa)

    base = 0
    for idx,field in enumerate(isa.fields):
        e, d, w = generate_encoder_decoder(field)
        encoding[idx] = e
        decoding[idx] = d
        fields_range[idx] = (base, base+w)
        base += w

    assert base == width

    def encode(inst):
        t = inst.value
        opcode = BitVector[width](0)
        base = 0
        for idx,v in enumerate(t):
            assert fields_range[idx][0] == base, (idx, base, fields_range[idx])
            v = BitVector[width](encoding[idx](v))
            opcode |= v << base
            base += fields_range[idx][1] - fields_range[idx][0]
        assert base == width
        return opcode

    def decode(opcode):
        args = []
        idx_ = -1
        for idx,d in decoding.items():
            assert idx > idx_
            base, top = fields_range[idx]
            args.append(d(opcode[base:top]))
            idx_ = idx
        return isa(*args)

    return encode, decode, width

def _sum(isa : Sum):
    encoding = {}
    decoding = {}
    width = get_width(isa)
    tag_width = len(isa.fields).bit_length()

    for tag, field in enumerate(isa.fields):
        tag = BitVector[tag_width](tag)
        e, d, w = generate_encoder_decoder(field)
        assert tag_width + w <= width
        encoding[field] = tag, e,
        decoding[tag] = d, w

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

    return encode, decode, width

def _bv(isa : AbstractBitVector):
    def encode(inst):
        return inst
    def decode(inst):
        return inst
    return encode, decode, get_width(isa)


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

