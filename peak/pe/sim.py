from hwtypes import BitVector, SIntVector
from peak import Peak
from .mode import gen_register_mode
from .cond import cond
from .lut import lut
from .isa import *

def gen_pe(num_inputs):

    class PE(Peak):

        def __init__(self):
            # Data registers
            self.data = [(gen_register_mode(Data)()) for i in range(num_inputs)]

            # Bit Registers
            self.bit0 = gen_register_mode(Bit)()
            self.bit1 = gen_register_mode(Bit)()
            self.bit2 = gen_register_mode(Bit)()

        def __call__(self, inst: Inst, \
                        data, \
                        bit0: Bit = Bit(0), \
                        bit1: Bit = Bit(0), \
                        bit2: Bit = Bit(0), \
                        clk_en: Bit = Bit(1)):

            # LUT part of the instruction
            lutinst = inst.lut
            bit0 = self.bit0(lutinst.bit0_mode, lutinst.bit0_const,
                              bit0, clk_en)
            bit1 = self.bit1(lutinst.bit1_mode, lutinst.bit1_const,
                              bit1, clk_en)
            bit2 = self.bit2(lutinst.bit2_mode, lutinst.bit2_const,
                              bit2, clk_en)
            lut_res = lut(lutinst.table, bit0, bit1, bit2)

            # ALU part of the instruction
            _, aluinst = inst.alu.match()
            data = [self.data[i](aluinst.data_modes[i],
                                 aluinst.data_consts[i], data[i],
                                 clk_en) for i in range(num_inputs)]
            alu_res, alu_res_p, C, V = aluinst.eval(*(data + [bit0]))
            Z = alu_res == 0
            N = Bit(alu_res[-1])

            # Cond part of instruction
            res_p = cond(inst.cond, alu_res, lut_res, Z, N, C, V)
            irq = Bit(0)

            return alu_res, res_p, irq

    return PE


