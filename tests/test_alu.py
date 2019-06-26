from peak import PeakNotImplementedError
from examples.alu import gen_alu, Inst, ALUOP
from hwtypes import BitVector

ALU = gen_alu(BitVector.get_family(),width=16)
alu = ALU()
Data = BitVector[16]

def test_add():
    inst = Inst(ALUOP.Add)
    assert Data(9) == alu(inst,Data(4), Data(5))
    assert Data(1) == alu(inst,Data(0), Data(1))
    try:
        #Need an object that has an alu_op field
        class A:
            alu_op = 5

        alu(A,Data(4),Data(5))
    except PeakNotImplementedError:
        pass
    except:
        print("Did not raise correct error")
        assert 0


if  __name__ == '__main__':
    test_add()

