from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from peak.assembler.assembler_util import _issubclass
from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
import examples.pico.asm as pico_asm

from hwtypes import BitVector, Bit
from hwtypes import make_modifier
from hwtypes.adt import Product, Tuple, Sum, Enum
import pytest

FooBV = make_modifier('Foo')(BitVector)
BarBV = make_modifier('Bar')(BitVector)

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
    assert hasattr(AA, "from_subfields")
    AB = AssembledADT[B, Assembler, BitVector]
    assert hasattr(AB, "from_subfields")
    AT = AssembledADT[T, Assembler, BitVector]
    assert hasattr(AT, "from_subfields")
    AS = AssembledADT[S, Assembler, BitVector]
    assert hasattr(AS, "from_subfields")

    #This is really what I want to do. 
    aa = AA.from_subfields(
        a=Bit(0),
        b=BV(3),
        e=E.b
    )
    assert aa == AA(a)
    assert aa.a == Bit(0)
    assert aa.b == BV(3)
    assert aa.e == E.b

    ab = AB.from_subfields(
        a=aa,
        b=Bit(1)
    )
    assert ab == AB(b)
    assert ab.a == aa
    assert ab.b == Bit(1)

    at = AT.from_subfields(aa, e)
    assert at == AT(t)
    assert at[0] == aa
    assert at[1] == e

    as_b = AS.from_subfields(ab)
    as_t = AS.from_subfields(t)
    assert as_b == AS(s_b)
    assert as_t == AS(s_t)
    assert as_b.match(B)
    assert not as_b.match(T)
    assert as_b[B] == ab
    assert as_t.match(T)
    assert not as_t.match(B)
    assert as_t[T] == at

@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa])
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
    assert s.match(I0)
    assert type(s.match(I0)) is Bit
    assert ~s.match(I1)
    assert type(~s.match(I1)) is Bit
    assert s[I0] == I0.a
    assert type(s[I0] == I0.a) is Bit
    assert s[I0] != I0.b
    assert type(s[I0] != I0.b) is Bit


    class Foo: pass
    with pytest.raises(TypeError):
        s.match(Foo)

    # The following rely on implementation details of Assembler
    # But the point is that S[I1] will return garbage
    # specificall I0.a extended to the size of I1
    assert s[I1] == BitVector[2](0)
    assert s[I1] != I1.c
    assert s[I1] != I1.d
