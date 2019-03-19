from .adt import Enum, ISABuilder, Product, Sum, Tuple
import typing as tp
from collections import OrderedDict
from functools import reduce
from hwtypes import AbstractBitVector, BitVector, AbstractBit, Bit
import operator

def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

def get_width(isa : ISABuilder):
    if _issubclass(isa, Enum):
        width = 0
        for e in map(lambda x : x.value, isa):
            if isinstance(e, int):
                width = max(width, e.bit_length())
            elif isinstance(e, AbstractBitVector):
                width = max(width, e.size)
            elif isinstance(e, bool):
                width = max(width, 1)
            elif isinstance(e, AbstractBit):
                width = max(width, 1)
            else:
                raise TypeError()
        return width
    elif _issubclass(isa, (Tuple, Product)):
        return sum(map(get_width, isa.fields))
    elif _issubclass(isa, Sum):
        return  max(map(get_width, isa.fields)) + len(isa.fields).bit_length()
    elif _issubclass(isa, AbstractBitVector):
        return isa.size
    elif _issubclass(isa, AbstractBit) or isinstance(isa, AbstractBit):
        return 1
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
    width = get_width(isa)
    for inst in isa:
        layout[inst] = (0, width, None)
        opcode = BitVector[width](inst.value)
        encoding[inst] = opcode
        decoding[opcode]  = inst

    def assembler(inst):
        return encoding[inst]
    def disassembler(bv):
        return decoding[bv]

    return assembler, disassembler, width, layout

def _product(isa : Product):
    encoding = {}
    decoding = {}
    layout = {}

    width = get_width(isa)

    base = 0
    for name,field in isa._fields_dict.items():
        e, d, w, l = generate_assembler(field)
        encoding[name] = e
        decoding[name] = d
        layout[name] = (base, base+w, l)
        base += w

    assert base == width

    def assembler(inst):
        opcode = BitVector[width](0)
        for name,v in inst._as_dict().items():
            v = BitVector[width](encoding[name](v))
            opcode |= v << layout[name][0]
        return opcode

    def disassembler(opcode):
        args = []
        for name,d in decoding.items():
            base, top, _ = layout[name]
            args.append(d(opcode[base:top]))
        return isa(*args)

    return assembler, disassembler, width, layout

def _sum(isa : Sum):
    encoding = {}
    decoding = {}
    layout = {}
    width = get_width(isa)
    tag_width = len(isa.fields).bit_length()

    for tag, field in enumerate(isa.fields):
        tag = BitVector[tag_width](tag)
        e, d, w, l = generate_assembler(field)
        assert tag_width + w <= width
        encoding[field] = tag, e,
        decoding[tag] = d, w
        layout[field] = (tag_width, tag_width+w, l)

    def assembler(inst):
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

    def disassembler(opcode):
        tag = opcode[0:tag_width]
        d, w = decoding[tag]
        return isa(d(opcode[tag_width:tag_width + w]))

    return assembler, disassembler, width, layout

def _bv_field(isa : tp.Type[AbstractBitVector]):
    def assembler(inst):
        return inst
    def disassembler(opcode):
        return isa(opcode)
    return assembler, disassembler, get_width(isa), None

def _bv_const(isa : AbstractBitVector):
    T = type(isa)
    def assembler(inst):
        if inst != isa:
            return ValueError()
        return inst
    def disassembler(opcode):
        if opcode != isa:
            return ValueError()
        return T(opcode)
    return assembler, disassembler, get_width(isa), None

def generate_assembler(isa : ISABuilder):
    if _issubclass(isa, Enum):
        return _enum(isa)
    elif _issubclass(isa, Product):
        return _product(isa)
    elif _issubclass(isa, Sum):
        return _sum(isa)
    elif _issubclass(isa, AbstractBitVector):
        return _bv_field(isa)
    elif isinstance(isa, AbstractBitVector):
        return _bv_const(isa)
    elif _issubclass(isa, AbstractBit):
        return _bv(isa)
    elif isinstance(isa, AbstractBit):
        return _bv_const(isa)
    else:
        raise TypeError(isa)

