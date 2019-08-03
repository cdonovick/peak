import random
from collections import namedtuple
from examples.riscv import R32I
import examples.riscv.isa as isa
import examples.riscv.asm as asm
import pytest

inst = namedtuple("inst", ["name", "func"])

NVALUES = 4
def random32():
    return isa.Word(random.randint(0,1<<32-1))
testa32s = [random32() for i in range(NVALUES)]
testb32s = [random32() for i in range(NVALUES)]

def random12():
    return isa.Word(random.randint(0,1<<12-1))
testb12s = [random12() for i in range(NVALUES)]

def random20():
    return isa.Word(random.randint(0,1<<20-1))
testb20s = [random20() for i in range(NVALUES)]


@pytest.mark.parametrize("op", [
    inst('and_', lambda x, y: x&y),
    inst('or_',  lambda x, y: x|y),
    inst('xor',  lambda x, y: x^y),
    inst('add',  lambda x, y: x+y),
    inst('sub',  lambda x, y: x-y),
])
@pytest.mark.parametrize("a", testa32s)
@pytest.mark.parametrize("b", testb32s)
def test_alu_reg(op,a,b):
    rd, rs1, rs2 = 1, 2, 3
    inst = getattr(asm,op.name)(rd, rs1, rs2)
    riscv = R32I([inst])
    riscv.poke_reg(rs1,a)
    riscv.poke_reg(rs2,b)
    riscv()
    assert riscv.peak_pc() == 1
    assert riscv.peak_reg(rd) == op.func(a,b)

@pytest.mark.parametrize("op", [
    inst('andi', lambda x, y: x&y),
    inst('ori',  lambda x, y: x|y),
    inst('xori',  lambda x, y: x^y),
    inst('addi',  lambda x, y: x+y),
    inst('subi',  lambda x, y: x-y),
])
@pytest.mark.parametrize("a", testa32s)
@pytest.mark.parametrize("b", testb12s)
def test_alu_imm(op,a,b):
    rd, rs1 = 1, 2
    inst = getattr(asm,op.name)(rd, rs1, b)
    riscv = R32I([inst])
    riscv.poke_reg(rs1,a)
    riscv()
    assert riscv.peak_pc() == 1
    assert riscv.peak_reg(rd) == op.func(a,b)

@pytest.mark.parametrize("imm", testb20s)
def test_lui(imm):
    rd = 1
    inst = asm.lui(rd,imm)
    riscv = R32I([inst])
    riscv()
    assert riscv.peak_pc() == 1
    assert riscv.peak_reg(rd) == imm << 12

@pytest.mark.parametrize("data", testa32s)
def test_lw(data):
    addr = 1
    rd, rs1, offset = 1, 2, 0
    inst = asm.lw(rd,rs1,offset)
    riscv = R32I([inst])
    riscv.poke_reg(rs1,addr)
    riscv.poke_mem(addr+offset,data)
    riscv()
    assert riscv.peak_pc() == 1
    assert riscv.peak_reg(rd) == data

@pytest.mark.parametrize("data", testa32s)
def test_sw(data):
    addr = 1
    rs1, rs2, offset = 1, 2, 0
    inst = asm.sw(rs1,rs2,offset)
    riscv = R32I([inst])
    riscv.poke_reg(rs1,addr)
    riscv.poke_reg(rs2,data)
    riscv()
    assert riscv.peak_pc() == 1
    assert riscv.peak_mem(addr+offset) == data

@pytest.mark.parametrize("op", [
    inst('beq', lambda x, y: x==y),
    inst('bne', lambda x, y: x!=y),
    inst('bltu',  lambda x, y: x<y),
    inst('bgeu',  lambda x, y: x>=y),
    inst('blt',  lambda x, y: isa.SInt32(x)<isa.SInt32(y)),
    inst('bge',  lambda x, y: isa.SInt32(x)>=isa.SInt32(y)),
])
@pytest.mark.parametrize("a", testa32s)
@pytest.mark.parametrize("b", testb32s)
def test_branch(op, a, b):
    rs1, rs2 = 1, 2
    inst = getattr(asm,op.name)(rs1, rs2, 2)
    riscv = R32I([inst])
    riscv.poke_reg(rs1,a)
    riscv.poke_reg(rs2,b)
    riscv()
    assert riscv.peak_pc() == 2 if op.func(a,b) else 1
