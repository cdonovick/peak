from .isa import *

# acc &= mem[addr]
def and_(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(and_=AND(i, p, Addr(addr)))

# acc += mem[addr]
def tad(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(tad=TAD(i, p, Addr(addr)))

# mem[addr] = acc and  then set acc=0
def dca(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(dca=DCA(i, p, Addr(addr)))

# mem[addr]++ and skip next inst if mem[addr] == 0
def isz(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(isz=ISZ(i, p, Addr(addr)))

# jmp to addr
def jmp(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(jmp=JMP(i, p, Addr(addr)))

# mem[addr] = pc and then jmp to addr+1
def jms(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(jms=JMS(i, p, Addr(addr)))

# io instruction - not implemented
#def iot():
#    pass

def opr1(cla=0, cll=0, cma=0, cml=0, rar=0, ral=0, twice=0, iac=0):
    if ral and rar:
        print("opr1: ral and rar can't both be set")
    return Inst(opr=OPR(opr1=OPR1(Bit(cla), Bit(cll), Bit(cma), Bit(cml), Bit(rar), Bit(ral), Bit(twice), Bit(iac))))

# clear accumulator
def cla(**kwargs):
    return opr1(cla=1, **kwargs)

# complement accumulator
def cma(**kwargs):
    return opr1(cma=1, **kwargs)

# acc=-1
def sta():
    return opr1(cla=1, cma=1)

# acc=1
#   return opr1(cla=1, iac=1)


# clear lnk - lnk=0
def cll(**kwargs):
    return opr1(cll=1, **kwargs)

# complement lnk - lnk = ~lnk
def cml(**kwargs):
    return opr1(cml=1, **kwargs)

# set lnk - lnk=1
def stl():
    return opr1(cll=1, cml=1)

# acc[11] = lnk
def glk():
    return opr1(cla=1, rol=1)



# increment acc - acc++
def iac(**kwargs):
    return opr1(iac=1, **kwargs)

# rotate acc and lnk right
def rar(**kwargs):
    return opr1(rar=1, **kwargs)

# rotate acc and lnk right twice
def rtr(**kwargs):
    return opr1(rar=1, twice=1, **kwargs)

# logical shift right
def lsr():
    return opr1(cll=1, rar=1)

# rotate acc and lnk left
def ral(**kwargs):
    return opr1(ral=1, **kwargs)

# rotate acc and lnk left twice
def rtl(**kwargs):
    return opr1(ral=1, twice=1, **kwargs)

# logical shift left
def lsl():
    return opr1(cll=1, ral=1)

# no operation
def nop():
    return opr1()

# negate - complement accumulator and add 1 
def cia(**kwargs):
    return opr1(cma=1,iac=1,**kwargs)



# the left column cannot be combined with the right colum
#   sma spa
#   sza sna
#   snl szl
# if skipflag
#   skip = spa & sna & szl
# else
#   skip = sma | sza | znl
def opr2(cla=0, sma=0, sza=0, snl=0, spa=0, sna=0, szl=0, skip=0, osr=0, hlt=0):
    flags1 = sma or sza or snl 
    flags2 = spa or sna or szl 
    if flags1 and flags2:
        print("opr2: sma|sza|snl and spa|sna|szl can't both be set")
    if flags2:
        skip = 1
    return Inst(opr=OPR(opr2=OPR2(Bit(cla), Bit(sma|spa), Bit(sza|sna), Bit(snl|szl), Bit(skip), Bit(osr), Bit(hlt), Bit(0))))

# skip if acc zero
def sza(**kwargs):
    return opr2(sza=1, **kwargs)

# skip if acc not zero
def sna(**kwargs):
    return opr2(sna=1, **kwargs)

# skip if acc minus
def sma(**kwargs):
    return opr2(sma=1, **kwargs)

# skip if acc positive
def spa(**kwargs):
    return opr2(spa=1, **kwargs)

# skip if lnk zero
def szl(**kwargs):
    return opr2(szl=1, **kwargs)

# skip if lnk not zero
def snl(**kwargs):
    return opr2(snl=1, **kwargs)

# skip
def skp():
    return opr2(skip=1)

# halt
def hlt():
    return opr2(hlt=1)

