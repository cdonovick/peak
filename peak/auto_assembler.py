import typing as tp
from collections import OrderedDict
from functools import reduce
from hwtypes import AbstractBitVector, BitVector, AbstractBit, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple
from hwtypes.adt_meta import EnumMeta
import operator
import ast
import magma as m

def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

def get_width(isa):
    if _issubclass(isa, Enum):
        return _enum(isa)[2]
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

    free  = set()
    used  = set()
    i_map = {}
    for inst in isa.enumerate():
        if isinstance(inst.value, int):
            used.add(inst.value)
            i_map[inst] = inst.value
        else:
            assert isinstance(inst.value, EnumMeta.Auto)
            free.add(inst)
    c = 0
    while free:
        inst = free.pop()
        while c in used:
            c += 1
        used.add(c)
        i_map[inst] = c

    width = max(used).bit_length()
    for inst in isa.enumerate():
        layout[inst] = (0, width, None)
        opcode = BitVector[width](i_map[inst])
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
    for name,field in isa.field_dict.items():
        e, d, w, l = generate_assembler(field)
        encoding[name] = e
        decoding[name] = d
        layout[name] = (base, base+w, l)
        base += w

    assert base == width

    def assembler(inst):
        opcode = BitVector[width](0)
        for name,v in inst.value_dict.items():
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

def generate_assembler(isa):
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
        return _bv_field(isa)
    elif isinstance(isa, AbstractBit):
        return _bv_const(isa)
    else:
        raise TypeError(isa)


class ISABuilderAssembler(ast.NodeTransformer):
    def __init__(self, _locals, _globals):
        self._locals = _locals
        self._globals = _globals

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            try:
                value = eval(compile(ast.Expression(node.value),
                                     filename="<ast>", mode="eval"),
                             self._locals, self._globals)
                if getattr(value, "_is_magma_enum", False):
                    return ast.Call(
                        ast.Name("assemble", ast.Load()),
                        [node], []
                    )
            except NameError:
                pass
        return node


def assemble_values_in_func(assembler, peak_fn, _locals, _globals):
    func_def = m.ast_utils.get_ast(peak_fn).body[0]
    func_def = ISABuilderAssembler(_locals, _globals).visit(func_def)
    # Uncomment to see result of AST rewrite
    # import astor
    # print(astor.to_source(func_def))
    func_def = ast.fix_missing_locations(func_def)
    exec(compile(ast.Module([func_def]), filename="<ast>", mode="exec"),
         _locals, _globals)
    return _locals[peak_fn.__name__]
