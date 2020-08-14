
from peak import family

from ast_tools.passes import remove_asserts


# A bit of hack putting the def of word and idx here
# and not isa but it makes life easier
class _RiscFamily_mixin:
    @property
    def Word(self):
        return self.BitVector[32]

    @property
    def Idx(self):
        return self.BitVector[5]


class PyFamily(_RiscFamily_mixin, family.PyFamily):
    def get_register_file(fam_self):
        class RegisterFile:
            def __init__(self):
                self.rf = {fam_self.Idx(0): fam_self.Word(0)}

            def _load(self, idx):
                if not isinstance(idx, fam_self.Idx):
                    raise TypeError(idx)
                return self.rf[idx]

            load1 = _load
            load2 = _load

            def store(self, idx, value):
                if not isinstance(idx, fam_self.Idx):
                    raise TypeError(idx)
                elif not isinstance(value, fam_self.Word):
                    raise TypeError(value)
                elif idx != 0:
                    self.rf[idx] = value
        return RegisterFile


class SMTFamily(_RiscFamily_mixin, family.SMTFamily):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._passes = remove_asserts(), *self._passes
    def get_register_file(fam_self):
        class RegisterFile:
            def __init__(self):
                self.rs1 = fam_self.Word()
                self.rs2 = fam_self.Word()
                self.rd = fam_self.Word()

            def load1(self, idx):
                if not isinstance(idx, fam_self.Idx):
                    raise TypeError(f'{idx}::{type(idx)}, expected {fam_self.Idx}')
                return (idx != fam_self.Idx(0)).ite(self.rs1, fam_self.Word(0))

            def load2(self, idx):
                if not isinstance(idx, fam_self.Idx):
                    raise TypeError(idx)
                return (idx != fam_self.Idx(0)).ite(self.rs2, fam_self.Word(0))

            def store(self, idx, value):
                if not isinstance(idx, fam_self.Idx):
                    raise TypeError(idx)
                elif not isinstance(value, fam_self.Word):
                    raise TypeError(value)
                self.rd = (idx != fam_self.Idx(0)).ite(value, self.rd)

            def _set_rs1_(self, val):
                self.rs1 = val

            def _set_rs2_(self, val):
                self.rs2 = val

            def _set_rd_(self, val):
                self.rd = val

        return RegisterFile

