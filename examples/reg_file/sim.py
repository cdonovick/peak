from peak import Peak, name_outputs, family_closure, Const
from .isa import ISA_fc
from ..riscv.util import Initial
from ..riscv import family


@family_closure(family)
def RegPE_fc(family):
    RegisterFile = family.get_register_file()
    isa = ISA_fc.Py

    @family.assemble(locals(), globals())
    class RegPE(Peak):
        def __init__(self):
            self.register_file = RegisterFile()

        def __call__(self, inst: isa.Inst) -> None:
            if inst.b.match:
                binst = inst.b.value
                a = self.register_file.load1(binst.rs1)
                b = self.register_file.load2(binst.rs2)
                rd = binst.rd
                if binst.op == isa.BOp.Add:
                    c = a + b
                else:
                    assert binst.op == isa.BOp.Nor
                    c = ~(a | b)
            else:
                uinst = inst.u.value
                a = self.register_file.load1(uinst.rs1)
                rd = uinst.rd
                if uinst.op == isa.UOp.Inv:
                    c = ~a
                else:
                    assert uinst.op == isa.UOp.Mov
                    c = a

            self.register_file.store(rd, c)

    return RegPE


@family_closure(family)
def RegPE_mappable_fc(family):
    RegPE = RegPE_fc(family)
    isa = ISA_fc.Py
    Word = isa.Word


    @family.assemble(locals(), globals())
    class RegPE_mappable(Peak):
        def __init__(self):
            self.reg_pe = RegPE()

        @name_outputs(rd=Word)
        def __call__(self,
                     inst: Const(isa.Inst),
                     rs1: Word,
                     rs2: Word,
                     rd: Initial(Word),
                     ) -> Word:

            self._set_rs1_(rs1)
            self._set_rs2_(rs2)
            self._set_rd_(rd)
            self.reg_pe(inst)
            return self.reg_pe.register_file.rd

        def _set_rs1_(self, rs1):
            self.reg_pe.register_file._set_rs1_(rs1)

        def _set_rs2_(self, rs2):
            self.reg_pe.register_file._set_rs2_(rs2)

        def _set_rd_(self, rd):
            self.reg_pe.register_file._set_rd_(rd)

    return RegPE_mappable

