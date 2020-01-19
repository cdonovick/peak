from peak import Peak, RAM, gen_register
from .isa import gen_isa

def gen_fifo(family, width, depth):

    Word, Addr, Inst, asm = gen_isa(family, width, depth)

    class FIFO(Peak):

        def __init__(self):
            # Addr has an extra bit
            self.mem = RAM(Word, 1 << (Addr.size-1), [], Word(0))

            self.rdaddr = gen_register(Addr, Addr(0))(Word.get_family())()
            self.wraddr = gen_register(Addr, Addr(0))(Word.get_family())()

        def __call__(self, inst: Inst) -> Word:

            rdaddr = self.rdaddr(Addr(0),0)
            wraddr = self.wraddr(Addr(0),0)

            full = self.full()
            empty = self.empty()

            result = self.mem(rdaddr[0:-1], Word(0), 0)

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
            return (rdaddr[-1] != wraddr[-1]) and (rdaddr[0:-1] == wraddr[0:-1])

        # return number of entries
        def fill(self):
            rdaddr = self.rdaddr(0,0)
            wraddr = self.wraddr(0,0)
            return wraddr - rdaddr

    return Word, Addr, asm, FIFO


