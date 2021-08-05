import abc
from hwtypes import TypeFamily
from .formula_constructor import And, Or
from peak.family import SMTFamily

class IndexVar:
    def __init__(self, num_entries: int, name: str, SMT=SMTFamily()):
        self.num_entries = num_entries
        self.var = SMT.BitVector[self.var_len(num_entries)](prefix=name)
        self.SMT = SMT

    def match_index(self, i: int):
        if i not in range(self.num_entries):
            raise ValueError(f"Index {i} out of bounds")
        return (self.var == self.translate_index(self.num_entries, i))

    def decode(self, v: int):
        for i in range(self.num_entries):
            if v == self.translate_index(self.num_entries, i):
                return i
        raise ValueError("Invalid Decode")

    @abc.abstractmethod
    def is_valid(self):
        raise NotImplementedError()
        return Or([self.match_index(i) for i in range(self.num_entries)]).to_hwtypes()


    @staticmethod
    @abc.abstractmethod
    def var_len(num_entries: int):
        '''Get length of var given a number of entries'''
        raise NotImplementedError()

    @staticmethod
    @abc.abstractmethod
    def translate_index(num_entries: int, i: int):
        '''get the index value given an index i into num_entries'''
        raise NotImplementedError()


class OneHot(IndexVar):
    @staticmethod
    def var_len(num_entries: int):
        return num_entries

    @staticmethod
    def translate_index(num_entries: int, i: int):
        return 2**i

    def is_valid(self):
        return ((self.var & (self.var-1))==0) & (self.var!=0)

class Binary(IndexVar):
    @staticmethod
    def var_len(num_entries: int):
        return len(bin(num_entries-1))-2

    @staticmethod
    def translate_index(num_entries: int, i: int):
        return i

    def is_valid(self):
        if self.num_entries == 2**self.var_len(self.num_entries):
            return self.SMT.Bit(True)
        else:
            return self.var < self.num_entries

