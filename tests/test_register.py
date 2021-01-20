import random

import fault
import magma as m

from peak.family import MagmaFamily, PyFamily


def test_registeer():
    m_family = MagmaFamily()
    py_family = PyFamily()
    Data = py_family.BitVector[16]
    Bit = py_family.Bit
    m_Reg = m_family.gen_register(m_family.BitVector[16], 0)
    py_reg = py_family.gen_register(Data, 0)()
    tester = fault.Tester(m_Reg, m_Reg.CLK)

    for _ in range(32):
        en = random.randint(0, 1)
        val = Data.random(16)
        gold = py_reg(val, en)
        tester.circuit.en = en
        tester.circuit.value = val
        tester.circuit.O.expect(gold)
        tester.step(2)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])
