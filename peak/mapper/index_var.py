import abc
from hwtypes import TypeFamily

class IndexVar:
    def __init__(self, num_entries: int, name: str, family: TypeFamily):
        self.num_entries = num_entries
        self.var = family.SMTFamily().BitVector[self.var_len(num_entries)](prefix=name)

    def match_index(self, i: int):
        if i not in range(self.num_entries):
            raise ValueError(f"Index {i} out of bounds")
        return (self.var == self.translate_index(self.num_entries, i))

    def decode(self, v: int):
        for i in range(self.num_entries):
            if v == self.translate_index(self.num_entries, i):
                return i
        raise ValueError(f"Invalid Decode: {v}")

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

class Binary(IndexVar):
    @staticmethod
    def var_len(num_entries: int):
        return len(bin(num_entries))-2

    @staticmethod
    def translate_index(num_entries: int, i: int):
        return i

