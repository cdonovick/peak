from .isa import *

def inst(enqueue, dequeue):
    return Inst(enqueue, dequeue)

# simultaneously enqueue and dequeue
def endequeue(data):
    return inst(Enqueue(write=Write(data)), Dequeue(read=Read(Word(0))))

def enqueue(data):
    return inst(Enqueue(write=Write(data)), Dequeue(nop=NOP(Word(0))))

def dequeue():
    return inst(Enqueue(nop=NOP(Word(0))), Dequeue(read=Read(Word(0))))

def nop():
    return inst(Enqueue(nop=NOP(Word(0))), Dequeue(nop=NOP(Word(0))))
