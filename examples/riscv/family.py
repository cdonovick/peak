
from peak import family


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
    def get_register_file(self):
        class RegisterFile:
            def __init__(self):
                self.rf = {self.Idx(0): self.Word(0)}

            def _load(self, idx):
                if not isinstance(idx, self.Idx):
                    raise TypeError(idx)
                return self.rf[idx]

            load1 = _load
            load2 = _load

            def store(self, idx, value):
                if not isinstance(idx, self.Idx):
                    raise TypeError(idx)
                elif not isinstance(value, self.Word):
                    raise TypeError(value)
                elif idx != 0:
                    self.rf[idx] = value
        return RegisterFile

class SMTFamily(_RiscFamily_mixin, family.SMTFamily):
    def get_register_file(self):
        class RegisterFile:
            def __init__(self, rs1_val, rs2_val, rd_val):
                self.rs1 = rs1_val
                self.rs2 = rs2_val
                self.rd = rd_val

            def load1(self, idx):
                if not isinstance(idx, self.Idx):
                    raise TypeError(idx)
                return (idx != self.Idx(0)).ite(self.rs1, self.Word(0))

            def load2(self, idx):
                if not isinstance(idx, self.Idx):
                    raise TypeError(idx)
                return (idx != self.Idx(0)).ite(self.rs2, self.Word(0))

            def store(self, idx, value):
                if not isinstance(idx, self.Idx):
                    raise TypeError(idx)
                elif not isinstance(value, self.Word):
                    raise TypeError(value)
                self.rd = (idx != self.IDx(0)).ite(value, self.rd)

        return RegisterFile

