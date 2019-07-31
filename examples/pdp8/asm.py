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

def iot():
    pass

def opr1(cla=0, cll=0, cma=0, cml=0, rar=0, ral=0, twice=0, iac=0):
    return Inst(OPR(OPR1(Bit(cla), Bit(cll), Bit(cma), Bit(cml), Bit(rar), Bit(ral), Bit(twice), Bit(iac))))

def cla():
    return opr1(cla=1)

def opr2(cla=0, sma=0, sza=0, snl=0, skip=0, osr=0, hlt=0):
    return Inst(OPR(OPR2(Bit(cla), Bit(sma), Bit(sza), Bit(snl), Bit(skip), Bit(osr), Bit(hlt), Bit(0))))

def sza():
    return opr2(sza=1)

def sna():
    return opr2(sza=1, skip=1)



