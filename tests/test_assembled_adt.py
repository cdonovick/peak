from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from peak.assembler.assembler_util import _issubclass
from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
from examples.min_pe.isa import ISA_fc as gen_min_isa
import examples.pico.asm as pico_asm

from hwtypes import BitVector, Bit
from hwtypes import make_modifier
from hwtypes.adt import Product, Tuple, Sum, Enum
import pytest

FooBV = make_modifier('Foo')(BitVector)
BarBV = make_modifier('Bar')(BitVector)

_, _, min_isa = gen_min_isa(BitVector.get_family())

@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa, min_isa])
@pytest.mark.parametrize("bv_type", [BarBV, FooBV])
def test_assembled_adt(isa, bv_type):
    def _check_recursive(isa, bv_type):
        asm_adt = AssembledADT[isa, Assembler, bv_type]
        asm = Assembler(isa)

        for inst in isa.enumerate():
            opcode = asm.assemble(inst, bv_type=bv_type)
            assert asm_adt(inst) == asm_adt(opcode)
            assert issubclass(type(asm_adt(inst)._value_), bv_type)
            assert issubclass(type(asm_adt(opcode)._value_), bv_type)

            assert asm_adt(inst) == inst
            assert type(asm_adt(inst) == inst) is Bit
            assert asm_adt(inst) == opcode
            assert type(asm_adt(inst) == opcode) is Bit

            assert asm_adt(opcode) == inst
            assert type(asm_adt(opcode) == inst) is Bit
            assert asm_adt(opcode) == opcode
            assert type(asm_adt(opcode) == opcode) is Bit

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

def test_match():
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

def test_from_subfields():
    BV = BitVector[3]
    class E(Enum):
        a=1
        b=4

    e = E.b

    class A(Product):
        a = Bit
        b = BV
        e = E

    a = A(
        a=Bit(0),
        b=BV(3),
        e=e
    )

    class B(Product):
        a = A
        b = Bit

    b = B(
        a=a,
        b=Bit(1)
    )

    T = Tuple[A, E]
    t = T(a, e)

    S = Sum[B, T]
    s_b = S(b)
    s_t = S(t)

    AA = AssembledADT[A, Assembler, BitVector]
    assert hasattr(AA, "from_fields")
    AB = AssembledADT[B, Assembler, BitVector]
    assert hasattr(AB, "from_fields")
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_fields")
    AS = AssembledADT[S, Assembler, BitVector]
    assert hasattr(AS, "from_fields")

    #This is really what I want to do.
    aa = AA.from_fields(
        a=Bit(0),
        b=BV(3),
        e=E.b
    )
    assert aa == AA(a)
    assert aa.a == Bit(0)
    assert aa.b == BV(3)
    assert aa.e == E.b

    ab = AB.from_fields(
        a=aa,
        b=Bit(1)
    )
    assert ab == AB(b)
    assert ab.a == aa
    assert ab.b == Bit(1)

    at = AT.from_fields(aa, e)
    assert at == AT(t)
    assert at[0] == aa
    assert at[1] == e

    as_b = AS.from_fields(B, ab)
    as_t = AS.from_fields(T, t)
    assert as_b == AS(s_b)
    assert as_t == AS(s_t)
    assert as_b[B].match
    assert not as_b[T].match
    assert as_b[B].value == ab
    assert as_t[T].match
    assert not as_t[B].match
    assert as_t[T].value == at

