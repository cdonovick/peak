import typing as  tp
import operator
from .isa import *
import functools as ft
from peak import name_outputs, Peak

from hwtypes import TypeFamily

def gen_alu(family : TypeFamily, assembler_generator):
    Bit = family.Bit
    Data = family.BitVector[DATAWIDTH]

    class Alu(Peak):
        @name_outputs(res=Data,flag_out=Bit)
        def __call__(self, inst : INST, data0 : Data, data1 : Data):
            def alu(inst : ALU_INST, data0 : Data, data1 : Data, bit0 : Bit):
                assembler, disassembler, _, _ = assembler_generator(ALU_INST, bv_type=family.BitVector)
                is_add = assembler(ALU_INST.Add) == inst
                is_and = assembler(ALU_INST.And) == inst
                is_xor = assembler(ALU_INST.Xor) == inst
                is_shl = assembler(ALU_INST.Shft) == inst
                add_res, add_carry = data0.adc(data1, bit0)
                and_res = data0 & data1
                xor_res = data0 ^ data1
                shl_res = data0 << data1
                other_carry = Bit(0)

                res = is_add.ite(add_res,
                        is_and.ite(and_res,
                            is_xor.ite(xor_res,
                                is_shl.ite(shl_res, Data(0))
                            )
                        )
                    )
                carry = is_add.ite(add_carry, other_carry)
                zero = ~ft.reduce(operator.or_, res, Bit(0))
                return res, carry, zero

            assembler, _, _, layout = assembler_generator(INST, bv_type=family.BitVector)
            bit0 = Bit(0)
            alu_inst = inst[layout['ALU'][0]:layout['ALU'][1]]
            res, _, _ = alu(inst, data0, data1, bit0)
            flag_out = Bit(0)
            assert isinstance(flag_out, Bit)
            assert isinstance(res, Data)
            return res, flag_out

    return Alu
