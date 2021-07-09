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
    prefix = f"{ts}{opname}(\n"
    body = ",\n".join([_value_to_str(v, new_ts, indent) for v in vs])
    suffix = f"\n{ts})"
    return prefix + body + suffix

class And(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        assert len(self.values) > 0

    def serialize(self, ts="", indent="|   "):
        return _op_to_str(self.values, "And", ts, indent)

    def to_hwtypes(self):
        return and_reduce(_to_hwtypes(v) for v in self.values)

class Or(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        assert len(self.values) > 0

    def serialize(self, ts="", indent="|   "):
        return _op_to_str(self.values, "Or", ts, indent)

    def to_hwtypes(self):
        return or_reduce(_to_hwtypes(v) for v in self.values)

class Implies(FormulaConstructor):
    def __init__(self, p, q):
        self.p = p
        self.q = q

    def serialize(self, ts="", indent="|   "):
        return _op_to_str((self.p, self.q), "Implies", ts, indent)

    def to_hwtypes(self):
        return (~_to_hwtypes(self.p)) | _to_hwtypes(self.q)
