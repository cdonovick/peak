from peak import Peak, name_outputs, rebind_type, ReservedNameError, compile_magma, gen_register
from hwtypes import Bit, BitVector, Product
from examples.simple_seq import gen_seq
import magma as m
from magma.testing import check_files_equal
import pytest
import inspect
from utils import reset_magma

def compile_and_check(output_file, circuit_definition, target):
    m.compile(f"tests/test_magma/build/{output_file}", circuit_definition, output=target)
    if target in ["verilog", "coreir-verilog"]:
        suffix = "v"
    elif target == "coreir":
        suffix = "json"
    else:
        raise NotImplementedError()
    assert check_files_equal(__file__, f"build/{output_file}.{suffix}",
                             f"gold/{output_file}.{suffix}")

def pytest_generate_tests(metafunc):
    if 'target' in metafunc.fixturenames:
        #metafunc.parametrize("target", ["verilog", "coreir"])
        metafunc.parametrize("target", ["coreir"])

@reset_magma
def test_compile_magma():
    Reg5 = gen_register(BitVector[5], 7)
    Reg4 = gen_register(BitVector[4], 7)
    assert Reg5 is not Reg4
    r5 = compile_magma(Reg5)
    r4 = compile_magma(Reg4)
    assert r5 is not r4

@reset_magma
def test_reg(target):
    Reg5 = gen_register(BitVector[5], 7)
    Reg5_magma = compile_magma(Reg5)
    compile_and_check("simplereg5", Reg5_magma, target)

def gen_accum(width=16):
    Data = BitVector[width]
    Reg = gen_register(Data, 0)
    class Accum(Peak):
        def __init__(self):
            self.reg: Reg = Reg()

        def __call__(self, in_ : Data) -> Data:
            return self.reg(in_, Bit(1))

    return Accum

@reset_magma
def test_composition(target):
    accum = gen_accum(17)
    accum_magma = compile_magma(accum)
    compile_and_check("accum", accum_magma, target)

@reset_magma
def test_adt(target):

    Data = BitVector[16]
    class Instr(Product):
        a=Bit
        b=Data
    class Instr_magma(m.Product):
        a = m.Bit
        b = m.Bits[16]
    RegBit = gen_register(Bit, 0)

    class Foo(Peak):
        def __init__(self):
            self.s: RegBit = RegBit()
        def __call__(self, instr  : Instr) -> (Data,Bit):
            a = instr.a
            b = instr.b
            s = self.s(a,Bit(1))
            if a:
                return b, s
            else:
                return ~b, ~a
    Foo_magma = compile_magma(Foo,magma_adt_dict=dict(Instr=Instr_magma))
    compile_and_check("adt", Foo_magma, target)





