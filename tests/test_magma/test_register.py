from peak import gen_register, rebind_magma
from hwtypes import BitVector
import magma as m
import fault


def test_register():
    Reg2 = gen_register(BitVector[2],  1)
    print(Reg2)
    Reg_magma = rebind_magma(Reg2)
    tester = fault.Tester(Reg_magma, Reg_magma.CLK)
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
    tester.compile_and_run("verilator", directory="tests/test_magma/build")
