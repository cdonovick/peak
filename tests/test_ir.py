from peak import family_closure
from peak.ir import IR
from hwtypes import BitVector, Bit, UIntVector
from hwtypes import SMTBit
from hwtypes.adt import Product, Sum, Enum
from examples.smallir import gen_SmallIR
import pytest
from random import randint
from hwtypes.adt_util import rebind_type

def rand_value(width):
    return randint(0, 2**width-1)

def test_add_peak_instruction():
    class Input(Product):
        a = BitVector[16]
        b = BitVector[16]
        c = Bit

    class Output(Product):
        x = BitVector[16]
        y = Bit

    ir = IR()
    def fun(family, a, b, c):
        return c.ite(a, b), c

    ir.add_peak_instruction("Simple", Input, Output, fun)

    assert "Simple" in ir.instructions
    Simple_fc = ir.instructions["Simple"]
    assert isinstance(Simple_fc, family_closure)
    Simple = Simple_fc(Bit.get_family())
    InputBV = rebind_type(Input, Bit.get_family())
    OutputBV = rebind_type(Output, Bit.get_family())
    for name, t in InputBV.field_dict.items():
        assert Simple.input_t.field_dict[name] is t
    for name, t in OutputBV.field_dict.items():
        assert Simple.output_t.field_dict[name] is t

    simple = Simple()
    BV16 = BitVector[16]
    x, y = simple(BV16(5), BV16(6), Bit(1))
    assert x == BV16(5)
    assert y == Bit(1)

@pytest.mark.parametrize("family", [Bit.get_family(), SMTBit.get_family()])
@pytest.mark.parametrize("args", [
    (rand_value(16), rand_value(16))
        for _ in range(20)
])
def test_smallir(family, args):
    args = [family.BitVector[16](val) for val in args]

    #IR
    ir = gen_SmallIR(16)
    
    for name, fun in (
        ("Add",  lambda x, y: x+y),
        ("Sub",  lambda x, y: x-y),
        ("And",  lambda x, y: x&y),
        ("Nand", lambda x, y: ~(x&y)),
        ("Or",   lambda x, y: (x|y)),
        ("Nor",  lambda x, y: ~(x|y)),
        ("Mul",  lambda x, y: x*y),
        ("Shftr", lambda x, y: x>>y),
        ("Shftl", lambda x, y: x<<y),
        ("Not",  lambda x: ~x),
        ("Neg",  lambda x: -x),
    ):
        Instr_fc = ir.instructions[name]
        Instr = Instr_fc(family)
        instr = Instr()
        if name in ("Not", "Neg"):
            gold = fun(args[0])
            ret = instr(args[0])
        else:
            gold = fun(args[0], args[1])
            ret = instr(args[0], args[1])
        assert gold == ret
