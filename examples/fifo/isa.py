from hwtypes import BitVector
from hwtypes.adt import TaggedUnion, Product
from hwtypes.modifiers import new

WIDTH = 32
Word = new(BitVector, 32, name="Word")

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

