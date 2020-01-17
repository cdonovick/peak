from hwtypes import BitVector
from .isa import Inst, Enqueue, Dequeue, Write, Read, Word
from peak import Peak, RAM, gen_register


def gen_fifo(Word, logn):
    n = 1 << logn
    Addr = BitVector[logn+1]
    AddrZero = Addr(0)

    Zero = Word(0)

    class FIFO(Peak):

        def __init__(self):
            family = Bit.get_family()
            self.mem = RAM(Inst, n, [], default_init=Zero)

            self.rdaddr = gen_register2(family, Addr, AddrZero)
            self.wraddr = gen_register2(family, Addr, AddrZero)

        def __call__(self, inst: Inst) -> Word:

            rdaddr = self.rdaddr(Addr(0),0)
            wraddr = self.wraddr(Addr(0),0)

            full = self.full()
            empty = self.empty()

            result = self.mem(rdaddr[0:-1], Zero, 0)

            dequeue = inst.dequeue
            read = dequeue.read.match
            if read:
                if not empty:
                    self.rdaddr(rdaddr+1, 1)

            enqueue = inst.enqueue
            if enqueue.write.match:
                if not full or read:
                    self.mem(wraddr[0:-1], enqueue.write.value.data, 1)
                    self.wraddr(wraddr+1, 1)

            return result

        # empty when both pointers point to the same location
        def empty(self):
            rdaddr = self.rdaddr(0,0)
            wraddr = self.wraddr(0,0)
            return rdaddr == wraddr

        # full when wraddr-rdaddr=N, or when low-order bits are
        # identical and high bit is different
        def full(self):
            rdaddr = self.rdaddr(0,0)
            wraddr = self.wraddr(0,0)
            #return self.rdaddr(0,0) == self.wraddr(0,0) + 1
            return (rdaddr[-1] != wraddr[-1]) and (rdaddr[0:-1] == wraddr[0:-1])

        # return number of entries
        def fill(self):
            rdaddr = self.rdaddr(0,0)
            wraddr = self.wraddr(0,0)
            return wraddr - rdaddr

    return FIFO


