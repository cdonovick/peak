from hwtypes import BitVector, Bit
from peak import Peak, name_outputs
from peak.family import PyFamily
from peak.register import gen_update_register

Data = BitVector[16]

def test_ports():

    class Adder(Peak, gen_ports=True):
        @name_outputs(c=Data)
        def __call__(self, a: Data, b: Data) -> Data:
            return a+b

    class Top(Peak, gen_ports=True):
        def __init__(self):
            self.a1 = Adder()
            self.a2 = Adder()
            self.a3 = Adder()

        @name_outputs(c=Data)
        def __call__(self, a: Data, b: Data) -> Data:
            self.a1.a @= a
            self.a1.b @= a

            self.a2.a @= b
            self.a2.b @= b

            self.a3.a @= self.a1.c
            self.a3.b @= self.a2.c

            return self.a3.c

    t = Top()
    t.a @= Data(1)
    t.b @= Data(2)
    t._eval_()
    assert t.c == Data(6)
    t._eval_()
    assert t.c == Data(6)
    t.a @= Data(3)
    assert t.c == Data(6)
    t._eval_()
    assert t.c == Data(10)


def test_reg():
    Reg = gen_update_register(Data, 0).Py

    class Counter(Peak, gen_ports=True):
        def __init__(self):
            self.reg = Reg()

        @name_outputs(out=Data)
        def __call__(self, en: Bit) -> Data:
            self.reg.value @= self.reg.out + 1
            self.reg.en @= en
            return self.reg.out


    counter = Counter()
    counter.en @= Bit(0)

    counter._step_()
    assert counter.out == 0
    counter._step_()
    assert counter.out == 0

    counter.en @= Bit(1)
    counter._step_()
    assert counter.out == 0
    counter.en @= Bit(0)
    counter._step_()
    assert counter.out == 1
    counter.en @= Bit(1)
    counter._step_()
    assert counter.out == 1
    counter._step_()
    assert counter.out == 2
