from peak import gen_register, compile_magma
from hwtypes import BitVector
import magma as m
import fault
from utils import reset_magma

@reset_magma
def test_register():
    m.backend.coreir_.CoreIRContextSingleton().reset_instance()
    print("Starting testreg")
    Reg2 = gen_register(BitVector[2],  1)
    Reg2_magma = compile_magma(Reg2)
    assert len(type(Reg2_magma.value))
    print(Reg2_magma)
    tester = fault.Tester(Reg2_magma, Reg2_magma.CLK)
    tester.circuit.ASYNCRESET = 0
    tester.eval()
    tester.circuit.ASYNCRESET = 1
    tester.eval()
    tester.circuit.ASYNCRESET = 0
    tester.eval()
    tester.circuit.value = 0
    tester.circuit.en = 0
    tester.step(2)
    tester.circuit.O.expect(1)
    tester.circuit.value = 2
    tester.circuit.en = 1
    tester.step(2)
    tester.circuit.O.expect(2)
    tester.circuit.en = 0
    tester.circuit.value = 3
    tester.step(2)
    tester.circuit.O.expect(2)
    tester.compile_and_run("verilator", directory="build")
