from .isa import *

def and_(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(AND(i, p, Addr(addr)))

def tad(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(TAD(i, p, Addr(addr)))

def dca(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(DCA(i, p, Addr(addr)))

def isz(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(ISZ(i, p, Addr(addr)))

def jmp(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(JMP(i, p, Addr(addr)))

def jms(addr, i=IA.DIRECT, p=MP.PAGE_ZERO):
    return Inst(JMS(i, p, Addr(addr)))

#def iot():
#    pass

def opr1(cla=0, cll=0, cma=0, cml=0, rar=0, ral=0, twice=0, iac=0):
    if ral and rar:
        print("opr1: ral and rar can't both be set")
    return Inst(OPR(OPR1(Bit(cla), Bit(cll), Bit(cma), Bit(cml), Bit(rar), Bit(ral), Bit(twice), Bit(iac))))

def cla():
    return opr1(cla=1)

def cma():
    return opr1(cma=1)

def cll():
    return opr1(cll=1)

def cml():
    return opr1(cml=1)

def rar():
    return opr1(rar=1)

def rtr():
    return opr1(rar=1, twice=1)

def ral():
    return opr1(ral=1)

def rtl():
    return opr1(ral=1, twice=1)

def nop():
    return opr1()



# the left column cannot be combined with the right colum
#   sma spa
#   sza sna
#   snl szl
# if skipflag
#   skip = spa & sna & szl
# else
#   skip = sma | sza | znl
def opr2(cla=0, sma=0, sza=0, snl=0, spa=0, sna=0, szl=0, osr=0, hlt=0):
    flags1 = sma or sza or snl 
    flags2 = spa or sna or szl 
    if flags1 and flags2:
        print("opr2: sma|sza|snl and spa|sna|szl can't both be set")
    skip = 1 if flags2 else 0
    return Inst(OPR(OPR2(Bit(cla), Bit(sma|spa), Bit(sza|sna), Bit(snl|szl), Bit(skip), Bit(osr), Bit(hlt), Bit(0))))

def sza():
    return opr2(sza=1)

def sna():
    return opr2(sna=1)

def sma():
    return opr2(sma=1)

def spa():
    return opr2(spa=1)

def szl():
    return opr2(szl=1)

def snl():
    return opr2(snl=1)

def hlt():
    return opr2(hlt=1)

