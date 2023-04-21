from operator import getitem

from hwtypes.adt_util import ADTVisitor
from hwtypes.adt_meta import GetitemSyntax, AttrSyntax



class Path:
    def __init__(self, *, path=()):
        self._p = path

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._p == other._p

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._p != other._p

    def __hash__(self):
        return hash(self._p)

    def __len__(self):
        return len(self._p)

    def push(self, getter, key):
        path = self._p + (getter, key)
        return Path(path=path)

    def pop():
        if not self:
            raise ValueError("popping empty path")
        path = self._p[:-1]
        return Path(path=path)

    def select(self, adt):
        for getter, key in self._path:
            adt = getter(adt, key)
        return adt

def solve(ir_fc, arch_fc, family_group):
    smt_fam = family_group.SMTFamily()
    ir_t = ir_fc(smt_fam)
    arch_t = arch_fc(smt_fam)
    arch_input_t = arch_t.input_t
    arch_output_t = arch_t.ouput_t



class LeafPaths(ADTVisitor):
    def __init__(self):
        self.path_to_leaf = {}
        self.current_path = Path()

    def visit_leaf(self, adt_t):
        self.path_to_leaf[self.current_path] = adt_t

    def generic_visit(self, adt_t):
        if isinstance(adt_t, AttrSyntax):
            getter = getattr
        elif  isinstance(adt_t, GetitemSyntax):
            getter = getitem
        else:
            assert 0

        path = self.current_path

        for k, v in adt_t.field_dict.items():
            assert getter(k, adt_t) == v
            self.current_path = path.push(getter, k)
            self.visit(v)

        self.current_path = path



