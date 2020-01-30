from .isa import *
from peak import Peak, gen_register2, RAM

ZERO = Bit(0)
ONE = Bit(1)

MAX_MEMORY = 4096


class PDP8(Peak):

    def __init__(self, mem):
        family = Bit.get_family()
        # 32 pages of 128 words
        self.mem = RAM(Inst, MAX_MEMORY, mem)
        self.pc = gen_register2(family, Word, Word(0))()
        self.acc = gen_register2(family, Word, Word(0))()
        self.lnk = gen_register2(family, Bit, ZERO)()
        self.running = gen_register2(family,Bit,ONE)()

    def __call__(self) -> None:
        if not self.is_running():
            return
        # phase 0
        pc = self.pc(0,0)
        inst = self.load(pc)
        pc = pc + 1

        if   inst.and_.match:
            and_ = inst.and_.value
            addr = self.addr(and_, pc)
            data = self.load(addr)
            self.acc(self.acc(0,0) & data, 1)
        elif inst.tad.match:
            tad = inst.tad.value
            addr = self.addr(tad, pc)
            data = self.load(addr).concat(BitVector[1](0))
            acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
            res = acc + data
            self.acc(res[0:WIDTH], 1)
            self.lnk(res[WIDTH], 1)
        elif inst.isz.match:
            isz = inst.isz.value
            addr = self.addr(isz, pc)
            data = self.load(addr) + 1
            self.store(addr, data)
            if data == 0:
                pc = pc + 1
        elif inst.dca.match:
            dca = inst.dca.value
            addr = self.addr(dca, pc)
            self.store(addr, self.acc(0,0))
            self.acc(Word(0),1)
        elif inst.jmp.match:
            jmp = inst.jmp.value
            addr = self.addr(jmp, pc)
            pc = addr
        elif inst.jms.match:
            jms = inst.jms.value
            addr = self.addr(jms, pc)
            self.store(addr,pc)
            pc = addr + 1
        elif inst.opr.match:
            opr = inst.opr.value
            if opr.opr1.match:
                opr1 = opr.opr1.value
                # Note that the order of these operations is specified
                if opr1.cla: # clear accumulator
                    self.acc(Word(0),1)
                if opr1.cma: # complement accumulator
                    self.acc(~self.acc(0,0),1)
                if opr1.cll: # clear link
                    self.lnk(ZERO,1)
                if opr1.cml: # complement link
                    self.lnk(~self.lnk(0,0),1)
                if opr1.iac: # increment accumulator
                    self.acc(self.acc(0,0)+1,1)
                if opr1.ral: # rotate left
                    acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
                    res = acc.bvrol(2 if opr1.twice else 1)
                    self.acc(res[0:WIDTH], 1)
                    self.lnk(res[WIDTH], 1)
                if opr1.rar: # rotate right
                    acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
                    res = acc.bvror(2 if opr1.twice else 1)
                    self.acc(res[0:WIDTH], 1)
                    self.lnk(res[WIDTH], 1)
            elif opr.opr2.match:
                opr2 = opr.opr2.value
                # Note that the order of these operations is specified
                if opr2.sma == ONE \
                or opr2.sza == ONE \
                or opr2.snl == ONE \
                or opr2.skip == ONE:
                    if opr2.skip == ZERO:
                        skip = ZERO
                        if opr2.sma == ONE: 
                            skip |= self.acc(0,0)[-1] == ONE
                        if opr2.sza == ONE:
                            skip |= self.acc(0,0) == Word(0)
                        if opr2.snl == ONE:
                            skip |= self.lnk(0,0) == ZERO
                    else:
                        skip = ONE
                        if opr2.sma == ONE \
                        or opr2.sza == ONE \
                        or opr2.snl == ONE:
                            if opr2.sma == ONE: # smp
                                skip &= self.acc(0,0)[-1] == ZERO
                            if opr2.sza == ONE: # sna
                                skip &= self.acc(0,0) != Word(0)
                            if opr2.snl == ONE: # szl
                                skip &= self.lnk(0,0) == ONE
                    if skip == ONE:
                        pc = pc + 1
                if opr2.cla:
                    self.acc(Word(0),1)
                if opr2.hlt:
                    self.running(ZERO, 1)

        self.pc(pc, 1)

    def addr(self, inst, pc):
        addr = inst.addr

        if inst.p == ZERO:
            page = BitVector[5](0)
        else:
            page = (pc-1)[7:]

        addr = Word(addr).concat(page) 

        # phase 1
        if inst.i == IA.INDIRECT:
            addr = self.load(addr)

        return addr

    def is_running(self):
        return self.running(0,0) == ONE

    def run(self):
        while self.is_running():
            self()

    def load(self, addr):
        return self.mem(addr, 0, 0)

    def store(self, addr, data):
        return self.mem(addr, data, 1)


    # testing interface to state

    def peak_pc(self):
        return int(self.pc(0,0))

    def poke_pc(self, value):
        return int(self.pc(Word(value), 1))

    def peak_acc(self):
        return int(self.acc(0, 0))

    def poke_acc(self, value):
        return int(self.acc(Word(value),1))

    def peak_lnk(self):
        return int(self.lnk(0,0))

    def poke_lnk(self, value):
        return int(self.lnk(Bit(value),1))

    def peak_mem(self, addr):
        return int(self.mem(Word(addr),0,0))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=Bit(1)))
