from hwtypes import BitVector, Bit
from hwtypes import make_modifier
from hwtypes.adt import TaggedUnion, Product, Tuple, Sum, Enum
from hwtypes.bit_vector_util import BitVectorProtocol

import pytest

from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from peak.assembler.assembler_util import _issubclass

from peak.assembler2.assembler import Assembler as Assembler2
from peak.assembler2.assembled_adt import AssembledADT as AssembledADT2

from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
from examples.min_pe.isa import ISA_fc as gen_min_isa
import examples.pico.asm as pico_asm


FooBV = make_modifier('Foo')(BitVector)
BarBV = make_modifier('Bar')(BitVector)

_, _, min_isa = gen_min_isa(BitVector.get_family())

@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa, min_isa])
@pytest.mark.parametrize("bv_type", [BarBV, FooBV])
def test_assembled_adt(isa, bv_type, AssembledADT, Assembler):
    def _check_recursive(isa, bv_type):
        asm_adt = AssembledADT[isa, Assembler, bv_type]
        asm = Assembler(isa)

        assert issubclass(asm_adt, BitVectorProtocol)

        for inst in isa.enumerate():
            opcode = asm.assemble(inst, bv_type=bv_type)
            assert asm_adt._is_valid_(opcode)
            assert asm_adt(inst) == asm_adt(opcode)
            assert issubclass(type(asm_adt(inst)._value_), bv_type)
            assert issubclass(type(asm_adt(opcode)._value_), bv_type)

            assert asm_adt(inst) == inst
            assert type(asm_adt(inst) == inst) is Bit
            assert asm_adt(inst) == opcode
            assert type(asm_adt(inst) == opcode) is Bit
            assert isinstance(asm_adt(inst), BitVectorProtocol)

            assert asm_adt(opcode) == inst
            assert type(asm_adt(opcode) == inst) is Bit
            assert asm_adt(opcode) == opcode
            assert type(asm_adt(opcode) == opcode) is Bit
            assert isinstance(asm_adt(opcode), BitVectorProtocol)

        if _issubclass(isa, Sum):
            for field in isa.fields:
                assert asm_adt[field] is AssembledADT[field, Assembler, bv_type]
                if isinstance(field, (Sum, Tuple, Product)):
                    _check_recursive(field, bv_type)

        elif _issubclass(isa, Product):
            for name, field in isa.field_dict.items():
                assert getattr(asm_adt, name) is AssembledADT[field, Assembler, bv_type]
                if isinstance(field, (Sum, Tuple, Product)):
                    _check_recursive(field, bv_type)

        elif _issubclass(isa, Tuple):
            for idx, field in isa.field_dict.items():
                assert asm_adt[idx] is AssembledADT[field, Assembler, bv_type]
                if isinstance(field, (Sum, Tuple, Product)):
                    _check_recursive(field, bv_type)

        else:
            assert 0, f'_check_recursive should not be called on {isa}'

    _check_recursive(isa, bv_type)


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
def test_match(AssembledADT, Assembler):
    class I0(Enum):
        a = 0
        b = 1

    class I1(Enum):
        c = 2
        d = 3

    class S(Sum[I0, I1]):
        pass

    asm_adt = AssembledADT[S, Assembler, BitVector]

    s = asm_adt(S(I0.a))
    assert s[I0].match
    assert type(s[I0].match) is Bit
    assert ~s[I1].match
    assert type(~s[I1].match) is Bit
    assert s[I0].value == I0.a
    assert type(s[I0].value == I0.a) is Bit
    assert s[I0].value != I0.b
    assert type(s[I0].value != I0.b) is Bit


    class Foo: pass
    with pytest.raises(KeyError):
        s[Foo]

    # The following rely on implementation details of Assembler
    # But the point is that S[I1] will return garbage
    # specificall I0.a extended to the size of I1
    assert s[I1].value == BitVector[2](0)
    assert s[I1].value != I1.c
    assert s[I1].value != I1.d


BV = BitVector[3]

class E(Enum):
    a=1
    b=4

T = Tuple[BV, Bit]

class P(Product):
    a = Bit
    b = BV

S = Sum[BV, Bit]

class TU(TaggedUnion):
    a = Bit
    b = BV


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("T, args",
        [
            (E, (E.a,)),
            (E, (E.b,)),
        ]
)
def test_from_fields_enum(T, args, AssembledADT, Assembler):
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")

    lit = T(*args)
    assembled = AT(lit)
    assembled_ = AT(assembled)
    from_fields = AT.from_fields(*args)

    assert lit == assembled_
    assert assembled == assembled_
    assert assembled_ == from_fields
    assert from_fields == lit


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("T, args",
        [
            (T, (BV(7), Bit(1))),
        ]
)
def test_from_fields_tuple(T, args, AssembledADT, Assembler):
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")

    lit = T(*args)
    assembled = AT(lit)
    assembled_ = AT(assembled)
    from_fields = AT.from_fields(*args)

    assert lit == assembled_
    assert assembled == assembled_
    assert assembled_ == from_fields
    assert from_fields == lit

    for i, v in enumerate(args):
        assert lit[i] == v
        assert assembled[i] == v
        assert assembled_[i] == v
        assert from_fields[i] == v


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("T, args",
        [
            (S, (Bit, Bit(0))),
            (S, (BV, BV(4))),
        ]
)
def test_from_fields_sum(T, args, AssembledADT, Assembler):
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")

    lit = T(args[1])
    assembled = AT(lit)
    assembled_ = AT(assembled)
    from_fields = AT.from_fields(*args)

    assert lit == assembled
    assert assembled == assembled_
    assert assembled_ == from_fields
    assert from_fields == lit

    assert lit[args[0]].match
    assert assembled[args[0]].match
    assert assembled_[args[0]].match
    assert from_fields[args[0]].match

    assert lit[args[0]].value == args[1]
    assert assembled[args[0]].value == args[1]
    assert assembled_[args[0]].value == args[1]
    assert from_fields[args[0]].value == args[1]


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("T, kwargs",
        [
            (P, dict(a=Bit(1), b=BV(6))),
        ]
)
def test_from_fields_product(T, kwargs, AssembledADT, Assembler):
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")

    lit = T(**kwargs)
    assembled = AT(lit)
    assembled_ = AT(assembled)
    from_fields = AT.from_fields(**kwargs)

    assert lit == assembled_
    assert assembled == assembled_
    assert assembled_ == from_fields
    assert from_fields == lit

    for k, v in kwargs.items():
        assert getattr(lit, k) == v
        assert getattr(assembled, k) == v
        assert getattr(assembled_, k) == v
        assert getattr(from_fields, k) == v


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
@pytest.mark.parametrize("T, kwargs",
        [
            (TU, dict(a=Bit(0))),
            (TU, dict(b=BV(11))),
        ]
)
def test_from_fields_tagged(T, kwargs, AssembledADT, Assembler):
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")

    lit = T(**kwargs)
    assembled = AT(lit)
    assembled_ = AT(assembled)
    from_fields = AT.from_fields(**kwargs)

    assert lit == assembled_
    assert assembled == assembled_
    assert assembled_ == from_fields
    assert from_fields == lit

    for k, v in kwargs.items():
        assert getattr(lit, k).match
        assert getattr(assembled, k).match
        assert getattr(assembled_, k).match
        assert getattr(from_fields, k).match

        assert getattr(lit, k).value == v
        assert getattr(assembled, k).value == v
        assert getattr(assembled_, k).value == v
        assert getattr(from_fields, k).value == v


@pytest.mark.parametrize("AssembledADT, Assembler", [
        (AssembledADT, Assembler), (AssembledADT2, Assembler2)
    ])
def test_enum_error(Assembler, AssembledADT):
    AE = AssembledADT[E, Assembler, BitVector]

    with pytest.raises(TypeError):
        E(1)

    with pytest.raises(TypeError):
        AE(1)

    with pytest.raises(TypeError):
        AE.from_fields(1)
