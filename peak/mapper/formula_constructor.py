import operator
from functools import partial, reduce, lru_cache

or_reduce = partial(reduce, operator.or_)
and_reduce = partial(reduce, operator.and_)


class FormulaConstructor:
    indent = "|   "

    @staticmethod
    def _to_smt(v):
        if isinstance(v, FormulaConstructor):
            return v.to_smt()
        return v

    @staticmethod
    def print_value(v, ts):
        if isinstance(v, FormulaConstructor):
            v.pretty(ts)
        else:
            print(f"{ts}{v.value.serialize()},")

class AND(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        assert len(self.values) > 0

    def pretty(self, ts=""):
        new_ts = ts + FormulaConstructor.indent
        print(f"{ts}AND(")
        for v in self.values:
            FormulaConstructor.print_value(v, new_ts)
        print(f"{ts}),")

    def to_smt(self):
        return and_reduce(FormulaConstructor._to_smt(v) for v in self.values)

class OR(FormulaConstructor):
    def __init__(self, values: list):
        self.values = list(values)
        assert len(self.values) > 0

    def pretty(self, ts="  "):
        new_ts = ts + FormulaConstructor.indent
        print(f"{ts}OR(")
        for v in self.values:
            FormulaConstructor.print_value(v, new_ts)
        print(f"{ts}),")
    def to_smt(self):
        return or_reduce(FormulaConstructor._to_smt(v) for v in self.values)

class IMPLIES(FormulaConstructor):
    def __init__(self, p, q):
        self.p = p
        self.q = q

    def pretty(self, ts=""):
        new_ts = ts + FormulaConstructor.indent
        print(f"{ts}IMPLIES(")
        for s, v in (("P", self.p), ("Q", self.q)):
            print(f"{new_ts}{s} =")
            FormulaConstructor.print_value(v, new_ts + FormulaConstructor.indent)
        print(f"{ts}),")

    def to_smt(self):
        return (~FormulaConstructor._to_smt(self.p)) | FormulaConstructor._to_smt(self.q)
