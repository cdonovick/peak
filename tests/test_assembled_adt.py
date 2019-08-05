from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from peak.assembler.assembler_util import _issubclass
from examples.demo_pes.pe5.isa import INST as pe5_isa
from examples.arm.isa import Inst as arm_isa
from examples.pico.isa import Inst as pico_isa
import examples.pico.asm as pico_asm

from hwtypes import BitVector
from hwtypes import make_modifier
from hwtypes.adt import Product, Tuple, Sum, Enum
import pytest

FooBV = make_modifier('Foo')(BitVector)
BarBV = make_modifier('Bar')(BitVector)


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
            assert asm_adt(inst) == opcode

            assert asm_adt(opcode) == inst
            assert asm_adt(opcode) == opcode

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
    assert I0 in s
    assert I1 not in s
    assert s[I0] == I0.a
    assert s[I0] != I0.b


    class Foo: pass
    with pytest.raises(TypeError):
        Foo in s

    # The following rely on implementation details of Assembler
    # But the point is that S[I1] will return garbage
    # specificall I0.a extended to the size of I1
    assert s[I1] == BitVector[2](0)
    assert s[I1] != I1.c
    assert s[I1] != I1.d
