import random
from peak.bitfield import encode, size
from examples.pdp8 import PDP8, Word
import examples.pdp8.isa as isa
import examples.pdp8.asm as asm
import pytest

NVALUES = 4
def random12():
    return Word(random.randint(0,1<<12-1))
testvectors1 = [random12() for i in range(NVALUES)]
testvectors2 = [random12() for i in range(NVALUES)]

@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_and(a,b):
    addr = 1
    inst = asm.and_(addr)
    assert size(type(inst)) == 12
    bits = encode(inst)
    assert bits == 0x020
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,a)
    pdp8.poke_acc(b)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == a&b

@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_tad(a,b):
    addr = 1
    inst = asm.tad(addr)
    bits = encode(inst)
    assert bits == 0x21
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,a)
    pdp8.poke_acc(b)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == a+b

def test_lnk():
    addr = 4
    inst = asm.tad(addr)
    pdp8 = PDP8([asm.tad(addr),asm.cll(),asm.cml()])
    pdp8.poke_mem(addr,Word(0o7777))
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_lnk() == 1
    pdp8()
    assert pdp8.peak_lnk() == 0
    pdp8()
    assert pdp8.peak_lnk() == 1

def test_isz():
    addr = 1
    inst = asm.isz(addr)
    bits = encode(inst)
    assert bits == 0x22
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,0)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == 1

@pytest.mark.parametrize("a", testvectors1)
def test_dca(a):
    addr = 1
    inst = asm.dca(addr)
    bits = encode(inst)
    assert bits == 0x23
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,0)
    pdp8.poke_acc(a)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == a


def test_jms():
    addr = 2
    inst = asm.jms(addr)
    bits = encode(inst)
    assert bits == 0x44
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == 3
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == 1

def test_jmp():
    addr = 2
    inst = asm.jmp(addr)
    bits = encode(inst)
    assert bits == 0x45
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == addr

def test_cla():
    inst = asm.cla()
    bits = encode(inst)
    assert bits == 0x17
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_cma():
    inst = asm.cma()
    #bits = encode(inst)
    #assert bits == 0x17
    pdp8 = PDP8([inst])
    pdp8.poke_acc(0o7777)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_sza():
    inst = asm.sza()
    bits = encode(inst)
    assert bits == 0x4f
    pdp8 = PDP8([inst])
    pdp8.poke_acc(0)
    pdp8()
    assert pdp8.peak_pc() == 2

def test_sna():
    inst = asm.sna()
    bits = encode(inst)
    assert bits == 0x14f
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 2

def test_ral():
    inst = asm.ral()
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 2

def test_rtl():
    inst = asm.rtl()
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 4

def test_rar():
    inst = asm.rar()
    pdp8 = PDP8([inst])
    pdp8.poke_acc(4)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 2

def test_rtr():
    inst = asm.rtr()
    pdp8 = PDP8([inst])
    pdp8.poke_acc(4)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 1

# From https://bigdanzblog.wordpress.com/2014/05/27/creating-a-very-simple-pdp-8-assembler-pal8-program/
# Add 2 numbers
#    CLA            /Clear the accumulator
#    TAD A          /Add contents of memory location A to accumulator
#    TAD B          /Add contents of memory location B to accumulator
#    HLT            /Halt the CPU
#A,  0003           /Define A as %3
#B,  0004           /Define B as %4

def test_prog():
    A, B = 4, 5
    pdp8 = PDP8([asm.cla(),
                 asm.tad(A),
                 asm.tad(B),
                 asm.hlt()])
    pdp8.poke_mem(A,3)
    pdp8.poke_mem(B,4)
    pdp8.run()
    assert pdp8.peak_acc() == 7


# From https://www.grc.com/pdp-8/isp-musings.htm
# Or
#CLA            / clear accumulator (AC) since all we have is add!
#TAD   ArgOne   / add (TAD) the first argument to the just-zeroed AC
#CMA            / invert the bits of ArgOne (CMA = Compliment Accumulator)
#DCA   Temp     / deposit the intermediate value in a temporary memory cell
#               / (DCA = Deposit and Clear Accumulator)
#TAD   ArgTwo   / add (TAD) the second argument to the just-zeroed AC
#CMA            / invert the bits of the second argument, ArgTwo
#AND   Temp     / AND the second inverted arg with the first inverted arg
#CMA            / compliment the result of the AND to get the final result
#               / the accumulator is left with the boolean 'OR' of the args

# Xor1
#CLA            / clear accumulator (AC) since all we have is add!
#TAD   ArgOne   / add (TAD) the first argument to the just-zeroed AC
#CMA            / invert the bits of ArgOne (CMA = Compliment Accumulator)
#DCA   Temp     / deposit the intermediate value in a temporary memory cell
               #/ (DCA = Deposit and Clear Accumulator)
#TAD   ArgTwo   / add (TAD) the second argument to the just-zeroed AC
#CMA            / invert the bits of the second argument, ArgTwo
#AND   Temp     / AND the second inverted arg with the first inverted arg
#CMA            / compliment the result of the AND to get the final result
#DCA   Temp     / save the 'OR' of the two arguments

#TAD   ArgOne   / get the first argument again
#AND   ArgTwo   / AND it with the second argument
#CMA            / invert the AND of the two arguments
#AND   Temp     / and finally, AND the result of the OR with this second half
               #/ the accumulator now contains the XOR of ArgOne and ArgTwo

# Xor2
#CLA            / clear accumulator (AC) since all we have is add!
#TAD   ArgOne   / add (TAD) ArgOne to the just-zeroed AC
#AND   ArgTwo   / AND ArgTwo to determine where the carrys will be
#CLL RAL        / clear the LINK (CLL) and rotate the accumulator left (RAL)
#CMA IAC        / compliment (CMA) & increment (IAC) the accumulator (negate)
#TAD   ArgOne   / add the first argument to the negated accumulator
#TAD   ArgTwo   / and add the second argument as well
#               / the accumulator now contains the XOR of ArgOne & ArgTwo


