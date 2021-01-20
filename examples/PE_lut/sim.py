from peak import Peak, family_closure, Const
from .isa import gen_isa
from types import SimpleNamespace

def gen_sub_modules(width):
    isa_fc = gen_isa(width)

    @family_closure
    def modules_fc(family):
        isa = isa_fc(family)

        @family.assemble(locals(), globals())
        class LUT(Peak):
            def __call__(self, lut: isa.LUT_t, bit0: isa.Bit, bit1: isa.Bit, bit2: isa.Bit) -> isa.Bit:
                i = isa.IDX_t([bit0, bit1, bit2])
                i = i.zext(5)
                return ((lut >> i) & 1)[0]

        OP = isa.OP
        @family.assemble(locals(), globals())
        class ALU(Peak):
            def __call__(self, alu_inst: isa.AluInst, a: isa.Data, b: isa.Data, d: isa.Bit) -> isa.Data:

                a = isa.SData(a)
                b = isa.SData(b)
                op = alu_inst.op
                if op == OP.imm:
                    res = isa.SData(alu_inst.imm)
                elif op == OP.Add:
                    res = a + b
                else: # op == OP.Mux:
                    res = d.ite(a, b)
                return res



        return SimpleNamespace(**locals())

    return modules_fc

def gen_PE(width):
    sub_mods_fc = gen_sub_modules(width)

    @family_closure
    def PE_fc(family):
        modules = sub_mods_fc(family)
        isa = modules.isa
        @family.assemble(locals(), globals())
        class PE(Peak):
            def __init__(self):
                self.lut: modules.LUT = modules.LUT()
                self.alu: modules.ALU = modules.ALU()

            def __call__(self, inst: Const(isa.Inst), d0: isa.Data, d1: isa.Data, b0: isa.Bit, b1: isa.Bit, b2: isa.Bit) -> (isa.Data, isa.Bit):
                alu_out = self.alu(inst.alu_inst, d0, d1, b0)
                lut_out = self.lut(inst.lut, b0, b1, b2)
                return alu_out, lut_out
        return PE

    return PE_fc
