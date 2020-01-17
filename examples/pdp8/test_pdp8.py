import random
from hwtypes import int2seq, seq2int
from peak.bitfield import encode, size
from examples.pdp8 import PDP8, Word, WIDTH
import examples.pdp8.isa as isa
import examples.pdp8.asm as asm
import pytest


def random12():
    return Word(random.randint(0,1<<12-1))

NVALUES = 4
testvectors1 = [random12() for i in range(NVALUES)]
testvectors2 = [random12() for i in range(NVALUES)]

#@pytest.mark.skip(reason="size not part of bitfield")
def test_size():
    inst = asm.and_(0)
    assert size(type(inst)) == WIDTH

# compare palbart to encoder
#
# palbart inst.pal
# 
# see inst.lst for machine code
#
@pytest.mark.skip(reason="size not part of bitfield")
def test_assembler():
    def assemble(inst):
        # by convention, on the pdp8 bit=0 is the most-significant bit
        return encode(inst, reverse=True)

    addr = 1
    assert assemble(asm.and_(addr)) == 0o0000 + addr
    assert assemble(asm.tad(addr))  == 0o1000 + addr
    assert assemble(asm.isz(addr))  == 0o2000 + addr
    assert assemble(asm.dca(addr))  == 0o3000 + addr
    assert assemble(asm.jms(addr))  == 0o4000 + addr
    assert assemble(asm.jmp(addr))  == 0o5000 + addr

    # opr1
    assert assemble(asm.nop())  == 0o7000 
    assert assemble(asm.cla())  == 0o7200 
    assert assemble(asm.cma())  == 0o7040 
    assert assemble(asm.cll())  == 0o7100 
    assert assemble(asm.cml())  == 0o7020 
    assert assemble(asm.stl())  == 0o7120 
    assert assemble(asm.iac())  == 0o7001 
    assert assemble(asm.cia())  == 0o7041 
    assert assemble(asm.ral())  == 0o7004 
    assert assemble(asm.rtl())  == 0o7006 
    assert assemble(asm.lsl())  == 0o7104 
    assert assemble(asm.rar())  == 0o7010 
    assert assemble(asm.rtr())  == 0o7012 
    assert assemble(asm.lsr())  == 0o7110 

    # opr2
    assert assemble(asm.sma())  == 0o7500 
    assert assemble(asm.spa())  == 0o7510 
    assert assemble(asm.sza())  == 0o7440 
    assert assemble(asm.sna())  == 0o7450 
    assert assemble(asm.szl())  == 0o7430 
    assert assemble(asm.snl())  == 0o7420 
    assert assemble(asm.skp())  == 0o7410 
    assert assemble(asm.hlt())  == 0o7402 

@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_and(a,b):
    addr = 1
    inst = asm.and_(addr)
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
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,a)
    pdp8.poke_acc(b)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == a+b


def test_isz():
    addr = 1
    inst = asm.isz(addr)
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
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == 3
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == 1

def test_jmp():
    addr = 2
    inst = asm.jmp(addr)
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == addr

def test_cla():
    pdp8 = PDP8([asm.cla()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_cma():
    pdp8 = PDP8([asm.cma()])
    pdp8.poke_acc(0o7777)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_cll():
    pdp8 = PDP8([asm.cll()])
    pdp8.poke_lnk(1)
    pdp8()
    assert pdp8.peak_lnk() == 0

def test_cml():
    pdp8 = PDP8([asm.cml()])
    pdp8.poke_lnk(1)
    pdp8()
    assert pdp8.peak_lnk() == 0

def test_stl():
    pdp8 = PDP8([asm.stl()])
    pdp8.poke_lnk(0)
    pdp8()
    assert pdp8.peak_lnk() == 1

def test_iac():
    pdp8 = PDP8([asm.iac()])
    pdp8()
    assert pdp8.peak_acc() == 1

def test_cia():
    pdp8 = PDP8([asm.cia()])
    pdp8.poke_acc(0o7777)
    pdp8()
    assert pdp8.peak_acc() == 1

def test_sza():
    pdp8 = PDP8([asm.sza()])
    pdp8.poke_acc(0)
    pdp8()
    assert pdp8.peak_pc() == 2

def test_sna():
    pdp8 = PDP8([asm.sna()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 2

def test_ral():
    pdp8 = PDP8([asm.ral()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 2

def test_rtl():
    pdp8 = PDP8([asm.rtl()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 4

def test_rar():
    pdp8 = PDP8([asm.rar()])
    pdp8.poke_acc(4)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 2

def test_rtr():
    pdp8 = PDP8([asm.rtr()])
    pdp8.poke_acc(4)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 1

def test_page():
    addr = 1
    value = 0o7777
    inst = asm.tad(addr,p=asm.MP.CURRENT_PAGE)
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,Word(value))
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == value

def test_indirect():
    addr = 1
    data = 2
    value = 0o7777
    inst = asm.tad(addr,i=asm.IA.INDIRECT)
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,Word(data))
    pdp8.poke_mem(data,Word(value))
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == value

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

# From https://bigdanzblog.wordpress.com/2014/05/27/creating-a-very-simple-pdp-8-assembler-pal8-program/
# Add 2 numbers
#    CLA            /Clear the accumulator
#    TAD A          /Add contents of memory location A to accumulator
#    TAD B          /Add contents of memory location B to accumulator
#    HLT            /Halt the CPU
#A,  0003           /Define A as %3
#B,  0004           /Define B as %4

def test_prog_add():
    A, B = 4, 5
    code = [asm.cla(),
            asm.tad(A),
            asm.tad(B),
            asm.hlt()]
    pdp8 = PDP8(code)
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

def test_prog_or():
    data = 10
    A, B, C = data, data+1, data+2
    code = [asm.cla(),
            asm.tad(A),
            asm.cma(),
            asm.dca(C),
            asm.tad(B),
            asm.cma(),
            asm.and_(C),
            asm.cma(),
            asm.hlt()]
    pdp8 = PDP8(code)
    pdp8.poke_mem(A,3)
    pdp8.poke_mem(B,4)
    pdp8.run()
    assert pdp8.peak_acc() == 7

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

def test_prog_xor1():
    data = 14
    A, B, C = data, data+1, data+2
    code = [asm.cla(),
            asm.tad(A),
            asm.cma(),
            asm.dca(C),
            asm.tad(B),
            asm.cma(),
            asm.and_(C),
            asm.cma(),
            asm.dca(C),
            asm.tad(A),
            asm.and_(B),
            asm.cma(),
            asm.and_(C),
            asm.hlt()]
    pdp8 = PDP8(code)
    pdp8.poke_mem(A,3)
    pdp8.poke_mem(B,4)
    pdp8.run()
    assert pdp8.peak_acc() == 7

# Xor2
#CLA            / clear accumulator (AC) since all we have is add!
#TAD   ArgOne   / add (TAD) ArgOne to the just-zeroed AC
#AND   ArgTwo   / AND ArgTwo to determine where the carrys will be
#CLL RAL        / clear the LINK (CLL) and rotate the accumulator left (RAL)
#CMA IAC        / compliment (CMA) & increment (IAC) the accumulator (negate)
#TAD   ArgOne   / add the first argument to the negated accumulator
#TAD   ArgTwo   / and add the second argument as well
#               / the accumulator now contains the XOR of ArgOne & ArgTwo

def test_prog_xor2():
    data = 14
    A, B, C = data, data+1, data+2
    code = [asm.cla(),
            asm.tad(A),
            asm.and_(B),
            asm.opr1(cll=1, ral=1),
            asm.opr1(cma=1, iac=1),
            asm.tad(A),
            asm.tad(B),
            asm.hlt()]
    pdp8 = PDP8(code)
    pdp8.poke_mem(A,3)
    pdp8.poke_mem(B,4)
    pdp8.run()
    assert pdp8.peak_acc() == 7

# From https://en.wikipedia.org/wiki/PDP-8
#/Compare numbers in memory at OPD1 and OPD2
#            CLA CLL     /Must start with 0 in AC and link
#            TAD OPD1    /Load first operand into AC (by adding it to 0); link is still clear
#            CIA         /Complement, then increment AC, negating it
#            TAD OPD2    /AC now has OPD2-OPD1; if OPD2≥OPD1, sum overflows and link is set
#            SZL         /Skip if link is clear
#            JMP OP2GT   /Jump somewhere in the case that OPD2≥OPD1;
#                        /Otherwise, fall through to code below.

def test_prog_cmp():
    data = 14
    A, B = data, data+1
    code = [asm.cla(cll=1),
            asm.tad(A),
            asm.cia(),
            asm.tad(B),
            asm.hlt()]
    pdp8 = PDP8(code)
    pdp8.poke_mem(A,3)
    pdp8.poke_mem(B,4)
    pdp8.run()
    assert pdp8.peak_lnk() == 1
