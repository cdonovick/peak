from peak.register import gen_register2
import magma as m
import fault


def test_register():
    Reg = gen_register2(m.get_family(), m.Bits[2], 1)
    tester = fault.Tester(Reg, Reg.CLK)
    tester.circuit.CLK = 0
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
    tester.compile_and_run("verilator")
