from magma.bitutils import clog2
from hwtypes.adt import TaggedUnion, Product
from hwtypes.modifiers import new

def gen_isa(family, width, depth):
    Word = new(family.BitVector, width, name="Word")

    # add one more bit to address to handle empty/full condition
    logdepth = clog2(depth)
    Addr = new(family.BitVector, logdepth+1, name="Addr")

    class NOP(Product):
        data = Word

    class Write(Product):
        data = Word

    class Read(Product):
        data = Word

    #@tag({nop:0, write:1})
    class Enqueue(TaggedUnion):
        nop = NOP
        write = Write

    #@tag({nop:0, read:1})
    class Dequeue(TaggedUnion):
        nop = NOP
        read = Read

    class Inst(Product):
        enqueue = Enqueue
        dequeue = Dequeue

    class Assembler:
        def inst(self, enqueue, dequeue):
            return Inst(enqueue, dequeue)

        def nop(self):
            return self.inst(Enqueue(nop=NOP(Word(0))), 
                             Dequeue(nop=NOP(Word(0))))

        def enqueue(self, data):
            return self.inst(Enqueue(write=Write(data)),
                             Dequeue(nop=NOP(Word(0))))

        def dequeue(self):
            return self.inst(Enqueue(nop=NOP(Word(0))),
                             Dequeue(read=Read(Word(0))))

        # simultaneously enqueue and dequeue
        def endequeue(self, data):
            return self.inst(Enqueue(write=Write(data)),
                             Dequeue(read=Read(Word(0))))

    return Word, Addr, Inst, Assembler()

