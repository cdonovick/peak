import random

import hwtypes as hw
import fault
import magma as m
import pytest

from peak.family import MagmaFamily, PyFamily, PyXFamily
from peak import Peak, name_outputs, family_closure

def test_register():
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


def test_attr_register():
    @family_closure
    def counter_fc(family):
        Bit = family.Bit
        Data = family.BitVector[16]
        Reg = family.gen_attr_register(Data, 0)

        @family.assemble(locals(), globals())
        class Counter(Peak):
            def __init__(self):
                self.reg = Reg()

            @name_outputs(out=Data)
            def __call__(self, en: Bit, rst: Bit) -> Data:
                last = self.reg
                if rst:
                    self.reg = Data(0)
                elif en:
                    self.reg = self.reg + 1
                return last

        return Counter

    Data = PyFamily().BitVector[16]
    Bit = PyFamily().Bit

    CtrPy = counter_fc.Py
    ctr = CtrPy()
    reg = ctr.__dict__['reg']
    assert isinstance(ctr.reg, Data)
    assert not isinstance(reg, Data)
    gold_val = Data(0)

    for _ in range(32):
        en = Bit(random.randint(0, 1))
        rst = Bit(random.randint(0, 1))
        val = ctr(en, rst)

        assert val == gold_val
        if rst:
            gold_val = Data(0)
        elif en:
            gold_val = val + 1

    assert isinstance(ctr.reg, Data)
    assert reg is ctr.__dict__['reg']

    ctr = CtrPy()
    reg = ctr.__dict__['reg']
    CtrPyX = counter_fc.PyX
    ctrx = CtrPyX()
    regx = ctrx.__dict__['reg']
    assert isinstance(ctr.reg, Data)
    assert isinstance(ctrx.reg, Data)
    assert not isinstance(reg, Data)
    assert not isinstance(regx, Data)

    for _ in range(32):
        en = Bit(random.randint(0, 1))
        rst = Bit(random.randint(0, 1))
        gold_val = ctr(en, rst)
        val = ctrx(en, rst)
        assert val == gold_val

    assert isinstance(ctr.reg, Data)
    assert isinstance(ctrx.reg, Data)
    assert reg is ctr.__dict__['reg']
    assert regx is ctrx.__dict__['reg']

    CtrM = counter_fc(MagmaFamily())

    ctrx = CtrPyX()
    tester = fault.Tester(CtrM, CtrM.CLK)
    for _ in range(32):
        en = random.randint(0, 1)
        rst = random.randint(0, 1)
        gold = ctrx(en, rst)
        tester.circuit.en = en
        tester.circuit.rst = rst
        tester.circuit.O.expect(gold)
        tester.step(2)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])


def test_adt_reg():
    class State(hw.Enum):
        init  = 0
        busy  = 1
        ready = 2

    @family_closure
    def state_fc(family):
        Bit = family.Bit
        Data = family.BitVector[16]
        State_ = family.get_adt_t(State)
        Reg = family.gen_attr_register(State_, State.init)

        @family.assemble(locals(), globals())
        class StateMachine(Peak):
            def __init__(self):
                self.reg = Reg()

            @name_outputs(out=Data)
            def __call__(self, step: Bit) -> State:
                current = self.reg
                if current == State.init:
                    self.reg = State_(State.ready)
                elif step:
                    if current == State.busy:
                        self.reg = State_(State.ready)
                    else:
                        self.reg = State_(State.busy)
                return current
        return StateMachine

    Bit = PyFamily().Bit
    state_machine = state_fc.Py()
    state_machine_x = state_fc.PyX()
    gold = State.init

    for _ in range(32):
        step = Bit(random.randint(0, 1))
        val = state_machine(step)
        val_x = state_machine_x(step)

        assert gold == val
        assert val == val_x

        if gold == State.init:
            gold = State.ready
        elif step:
            if gold == State.busy:
                gold = State.ready
            else:
                gold = State.busy

    # Magma only supports bv registers
    with pytest.raises(TypeError):
        state_fc.Magma
