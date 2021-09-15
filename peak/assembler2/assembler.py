from collections import defaultdict
import functools as ft
import inspect
import operator
from types import MappingProxyType
import typing as tp


from .assembler_abc import AbstractAssembler
from hwtypes import AbstractBitVector, AbstractBit, BitVector, Bit
from hwtypes.adt import Enum, Product, Sum, Tuple, TaggedUnion
from hwtypes.adt_meta import BoundMeta, EnumMeta


from .assembler_util import _issubclass, _gen_is_valid


class Assembler(AbstractAssembler):
    _isa : BoundMeta

    def __init__(self, isa: BoundMeta):
        super().__init__(isa)
        if _issubclass(isa, Enum):
            asm, ff, dsm, extract, match, is_valid, width = _enum(isa)
        elif _issubclass(isa, (Tuple, Product)):
            asm, ff, dsm, extract, match, is_valid, width = _tuple(isa)
        elif _issubclass(isa, Sum):
            asm, ff, dsm, extract, match, is_valid, width = _sum(isa)
        elif _issubclass(isa, (AbstractBit, AbstractBitVector)):
            asm, ff, dsm, extract, match, is_valid, width = _field(isa)
        else:
            raise TypeError(f'isa: {isa}')
        self._from_fields = ff
        self._asm = asm
        self._dsm = dsm
        self._extract = extract
        self._is_valid = is_valid
        self._match = match
        self._width = width

    def __init_subclass__(cls, cache=True, **kwargs):
        super().__init_subclass__(**kwargs)

    @property
    def width(self) -> int:
        return self._width

    def assemble(self, inst: 'isa', bv_type: tp.Type[AbstractBitVector] = BitVector) -> AbstractBitVector:
        return self._asm(inst, bv_type)

    def disassemble(self, bv: BitVector) -> 'isa':
        return self._dsm(bv)

    def extract(self, bv: AbstractBitVector, field: tp.Union[str, int, type]) -> AbstractBitVector:
        return self._extract(bv, field)

    def match(self, bv: AbstractBitVector, field: tp.Union[str, type]) -> AbstractBit:
        return self._match(bv, field)

    def is_valid(self, opcode: AbstractBitVector) -> AbstractBit:
        return self._is_valid(opcode)

    def from_fields(self, *args, **kwargs) -> AbstractBitVector:
        return self._from_fields(*args, **kwargs)


def _create_from_layout(width, layout, field_bvs):
    if layout.keys() != field_bvs.keys():
        raise ValueError('layout does not match field_bvs')

    ranges = sorted(layout.values())
    if not all(
            type(r0) == type(r1) == tuple
            and len(r0) == len(r1) == 2
            # ranges are not overlapping and are bounded by (0, width)
            and 0 <= r0[0] < r0[1] <= r1[0] < r1[1] <= width
            for r0, r1 in zip(ranges, ranges[1:])):
        raise ValueError('invalid layout')

    T = None
    for v in field_bvs.values():
        if T is None:
            T = type(v).unsized_t
        else:
            assert T == type(v).unsized_t
    assert T is not None


    slots = [T[1]() for _ in range(width)]
    for field_name, (low, hi) in layout.items():
        # need to add None to keep the indexing consistent
        slots[low:hi] = field_bvs[field_name], *(None for _ in range(low+1, hi))
    bv = ft.reduce(T.concat, (s for s in slots if s is not None))
    assert bv.size == width, bv.size

    #Need to cast to T because magma concat doesn't maintain type
    return T[width](bv)


def _enum(isa: tp.Type[Enum]):
    asm_d: tp.Dict[Enum, int] = {}
    dsm_d: tp.Dict[int, Enum] = {}

    free  = []
    used = set()

    for inst in isa.enumerate():
        val = inst._value_
        if isinstance(val, int):
            if (val < 0):
                raise ValueError('Enum values must be > 0')
            asm_d[inst] = val
            dsm_d[val] = inst
            used.add(val)
        else:
            assert isinstance(val, EnumMeta.Auto)
            free.append(inst)

    c = 0
    for i in free:
        while c in used:
            c += 1
        used.add(c)
        asm_d[i] = c
        dsm_d[c] = i

    if not asm_d:
        raise TypeError('Enum must not be empty')

    opcodes = asm_d.values()

    width = max(opcodes).bit_length()

    def asm(inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        return bv_type[width](asm_d[inst])

    def from_fields(v):
        if isinstance(v, AbstractBitVector):
            return v
        else:
            raise TypeError('expected bitvector')

    def dsm(bv: BitVector):
        return dsm_d[bv.as_uint()]

    def extract(bv, field):
        raise TypeError('Enum has no fields to extract')

    def match(bv, field):
        return bv == asm_d[field]


    is_valid = _gen_is_valid(opcodes, width)

    return asm, from_fields, dsm, extract, match, is_valid, width


def _tuple(isa: tp.Type[Tuple]):

    layout = {}
    base = 0
    n2i = {}
    if issubclass(isa, Product):
        kT = (str, int)
        for k, (name, field) in enumerate(isa.field_dict.items()):
            field_width = Assembler(field).width
            n2i[name] = k
            layout[name] = layout[k] = _, base = (base, base + field_width)
    else:
        kT = (int,)
        for name, field in isa.field_dict.items():
            field_width = Assembler(field).width
            layout[name] = _, base = (base, base + field_width)


    width = base

    def asm(inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        opcode = bv_type[width](0)
        for name, field in isa.field_dict.items():
            assembler = Assembler(field)
            v = assembler.assemble(inst.value_dict[name], bv_type)
            v = _extend_to_width(v, width)
            opcode |= v << layout[name][0]
        return opcode

    if issubclass(isa, Product):
        def from_fields(*args, **kwargs):
            sig = inspect.signature(isa.__init__)
            # ... for self
            bound = sig.bind(..., *args, **kwargs)
            fields = {k: v for k, v in bound.arguments.items() if k != 'self'}
            # assert we are either using the int or string key for each range
            for name, k in n2i.items():
                assert name in fields or k in fields

            # layout has both int and string keys, filter to used ones
            layout_ = {k: v for k, v in layout.items() if k in fields}
            bv_value = _create_from_layout(width, layout_, fields)
            return bv_value
    else:
        def from_fields(*args):
            if len(args) != len(isa.fields):
                raise  TypeError('Incorrect number of positional arguments')
            fields = dict(enumerate(args))
            # layout has both int and string keys, filter to used ones
            layout_ = {k: v for k, v in layout.items() if k in fields}
            bv_value = _create_from_layout(width, layout_, fields)
            return bv_value

    def dsm(bv: BitVector):
        args = []
        for name,field in isa.field_dict.items():
            fbv = bv[slice(*layout[name])]
            args.append(Assembler(field).disassemble(fbv))
        return isa(*args)

    def extract(bv, field):
        if isinstance(field, kT):
            return bv[slice(*layout[field])]
        else:
            raise TypeError(f'{isa} has no field {field}')


    def match(bv, field):
        raise TypeError('Product has no fields to match')

    def is_valid(opcode: AbstractBitVector[width]) -> AbstractBit:
        args = []
        for name, field in isa.field_dict.items():
            idx = slice(*layout[name])
            args.append(Assembler(field).is_valid(opcode[idx]))
        return ft.reduce(operator.and_, args, opcode.get_family().Bit(1))

    return asm, from_fields, dsm, extract, match, is_valid, width

def _extend_to_width(bv, w):
    if w < bv.size:
        raise TypeError()

    return bv.zext(w - bv.size)

def _sum(isa: tp.Type[Sum]):
    name_to_field = {}
    name_to_tag = {}
    tag_to_name = {}
    # Tracks all the tags associated with a given field type
    # which may not be 1-1 in TaggedUnion
    field_to_tags = defaultdict(list)
    layout = {}
    tag_width = (len(isa.field_dict)-1).bit_length()
    tag_layout = (0, tag_width)

    sorted_fields = list(sorted(
        isa.field_dict.items(),
        key=repr
    ))

    payload_width = 0
    for tag, (name, field) in enumerate(sorted_fields):
        assert name not in name_to_field
        name_to_field[name] = field
        name_to_tag[name] = tag
        tag_to_name[tag] = name
        field_to_tags[field].append(tag)
        if field not in layout:
            assert len(field_to_tags[field]) == 1
            field_width = Assembler(field).width
            layout[field] = (tag_width, tag_width + field_width)
            layout[name] = (tag_width, tag_width + field_width)
            payload_width = max(payload_width, field_width)
        elif name not in layout:
            layout[name] = layout[field]

    max_tag = tag
    width = tag_width + payload_width

    tag_validators = {}
    for field, tags in field_to_tags.items():
        tag_validators[field] = _gen_is_valid(tags, tag_width)


    def asm(inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector[width]:
        for k, v in inst.value_dict.items():
            if v is not None:
                break
        else:
            raise AssertionError(f'Unreachable code, {inst} has no value')

        assert name_to_field[k] == type(v)
        field = type(v)
        payload = Assembler(field).assemble(v, bv_type)
        payload = _extend_to_width(payload, payload_width)
        tag = bv_type[tag_width](name_to_tag[k])
        opcode = tag.concat(payload)
        assert opcode.size == width, (opcode, width)
        return opcode


    def from_fields(*args, **kwargs):
        if issubclass(isa, TaggedUnion):
            if len(args) != 0 or len(kwargs) != 1:
                raise  TypeError('Expected exactly one keyword argument')

            name, value = kwargs.popitem()
        else:
            if len(args) != 2 or len(kwargs) != 0:
                raise  TypeError('Expected two positional arguments')

            name, value = args

        tag = name_to_tag[name]

        T = type(value)

        fields = {
            'value': value,
            'tag': T.unsized_t[tag_width](tag),
        }

        layout_ = {
            'value': layout[name],
            'tag': tag_layout,
        }

        bv_value = _create_from_layout(width, layout_, fields)
        return bv_value


    def dsm(bv: BitVector[width]):
        tag = bv[0:tag_width].as_uint()
        name = tag_to_name[tag]
        field = name_to_field[name]
        payload = bv[slice(*layout[field])]
        value = Assembler(field).disassemble(payload)
        value_dict = {k: value if k == name else None for k in isa.field_dict}
        return isa.from_values(value_dict)

    def extract(bv: AbstractBitVector[width], field) -> AbstractBitVector:
        return bv[slice(*layout[field])]

    def match(bv: AbstractBitVector[width], field) -> AbstractBit:
        tag_bv = bv[slice(*tag_layout)]
        false = bv.get_family().Bit(0)
        if isinstance(field, str):
            return  tag_bv == name_to_tag[field]
        else:
            return ft.reduce(operator.or_, (tag_bv == tag for tag in field_to_tags[field]), false)

    def is_valid(opcode: AbstractBitVector[width]) -> AbstractBit:
        tag = opcode[slice(*tag_layout)]
        valid = opcode.get_family().Bit(0)
        for field, validator in tag_validators.items():
            payload = opcode[slice(*layout[field])]
            valid_field = Assembler(field).is_valid(payload)
            valid_tag = validator(tag)
            valid |= (valid_tag & valid_field)
        return valid

    return asm, from_fields, dsm, extract, match, is_valid, width


def _field(isa : tp.Type[AbstractBitVector]):
    if _issubclass(isa, AbstractBitVector):
        width = isa.size
    elif _issubclass(isa, AbstractBit):
        width = 1
    else:
        raise TypeError()

    def asm(inst: 'isa', bv_type: tp.Type[AbstractBitVector]) -> AbstractBitVector:
        return bv_type[width](inst)

    def from_fields(v):
        if isinstance(v, AbstractBitVector):
            return v
        else:
            raise TypeError('expected bitvector')

    def dsm(bv: BitVector):
        return isa(bv)

    def extract(bv, field):
        raise TypeError(f'{isa} has no fields to extract')

    def match(bv, field):
        raise TypeError(f'{isa} has no fields to match')

    def is_valid(opcode):
        return opcode.get_family().Bit(1)

    return asm, from_fields, dsm, extract, match, is_valid, width
