from peak import Peak, name_outputs
from hwtypes import BitVector, SMTBitVector

def test_meta():
    x = 5
    stack = 4
    env = 3
    class A(Peak):
        def __init__(self):
            self.x = x
            self.stack = stack
    assert hasattr(A,"_env_")
    assert A._env_['x'] == 5
    assert A._env_['stack'] == 4
    assert A._env_['env'] == 3

def test_rebind():
    Data = BitVector[16]
    class B(Peak):
        def __init__(self):
            self.Data = Data
        def __call__(self,a : Data):
            return a + BitVector[16](5)
    assert Data(6) == B()(Data(1))
    B_smt = B.rebind(SMTBitVector.get_family())
    assert B_smt().Data == SMTBitVector[16]
    try:
        b_sym = B_smt()(SMTBitVector[16]())
        print(b_sym)
    except:
        assert 0
test_rebind()
