import operator
from functools import partial, reduce, lru_cache

or_reduce = partial(reduce, operator.or_)
and_reduce = partial(reduce, operator.and_)

class FormulaConstructor:
    pass

def _to_hwtypes(v):
    if isinstance(v, FormulaConstructor):
        return v.to_hwtypes()
    return v

def _value_to_str(v, ts, indent):
    if isinstance(v, FormulaConstructor):
        return v.serialize(ts, indent)
    else:
        return f"{ts}{v.value.serialize()}"

def _op_to_str(vs, opname, ts, indent):
    new_ts = ts + indent
    return "\n".join([
        f"{ts}{opname}(",
        ",\n".join([_value_to_str(v, new_ts, indent) for v in vs]),
        f"{ts})"
    ])
from hwtypes import SMTBit
def _check(vs):
    assert len(vs) > 0
    for v in vs:
        assert isinstance(v, FormulaConstructor) or isinstance(v, SMTBit)
class And(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        _check(self.values)

    def serialize(self, ts="", indent="|   "):
        return _op_to_str(self.values, "And", ts, indent)

    def to_hwtypes(self):
        return and_reduce(_to_hwtypes(v) for v in self.values)

class Or(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        _check(self.values)

    def serialize(self, ts="", indent="|   "):
        return _op_to_str(self.values, "Or", ts, indent)

    def to_hwtypes(self):
        return or_reduce(_to_hwtypes(v) for v in self.values)

class Implies(FormulaConstructor):
    def __init__(self, p, q):
        self.p = p
        self.q = q
        _check([p, q])

    def serialize(self, ts="", indent="|   "):
        return _op_to_str((self.p, self.q), "Implies", ts, indent)

    def to_hwtypes(self):
        return (~_to_hwtypes(self.p)) | _to_hwtypes(self.q)
