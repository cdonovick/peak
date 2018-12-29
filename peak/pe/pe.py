from bit_vector import BitVector, SIntVector
from .. import Peak
from .mode import RegisterMode
from .cond import cond
from .lut import lut
from .isa import *

def gen_pe(isa, num_inputs):

    class PE(Peak):

        def __init__(self):
            self.ops = isa.fields
            
            # Data registers
            self.regdata = [(RegisterMode(Data)) for i in range(num_inputs)]

            # Bit Registers
            self.regbit0 = RegisterMode(Bit)
            self.regbit1 = RegisterMode(Bit)
            self.regbit2 = RegisterMode(Bit)

        def alu(self, inst, args):
            res, res_p, C, V = inst.eval(*args)

            Z = res == 0
            N = Bit(res[-1])

            return res, res_p, Z, N, C, V

        def __call__(self, inst: Inst, \
                        data, \
                        bit0: Bit = Bit(0), \
                        bit1: Bit = Bit(0), \
                        bit2: Bit = Bit(0), \
                        clk_en: Bit = Bit(1)):

            data = [self.regdata[i](inst.data_mode[i],
                                    inst.data[i],
                                    data[i],
                                    clk_en) 
                                    for i in range(num_inputs)]

            bit0 = self.regbit0(inst.bit0_mode, inst.bit0, bit0, clk_en)
            bit1 = self.regbit1(inst.bit1_mode, inst.bit1, bit1, clk_en)
            bit2 = self.regbit2(inst.bit2_mode, inst.bit2, bit2, clk_en)

            alu_res, alu_res_p, Z, N, C, V = self.alu(inst, data + [bit0])

            lut_res = lut(inst.lut, bit0, bit1, bit2)
            res_p = cond(inst.cond, alu_res, lut_res, Z, N, C, V)
            irq = Bit(0)

            return alu_res, res_p, irq

    return PE


