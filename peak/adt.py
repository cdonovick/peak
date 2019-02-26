import itertools as it
import typing as tp
from dataclasses import is_dataclass, fields, dataclass
from enum import auto
from enum import Enum as pyEnum

__all__ =  ['Product', 'is_product', 'product']
__all__ += ['Sum', 'is_sum', 'new_instruction']


def _issubclass(sub : tp.Any, parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

class ISABuilder:
    @staticmethod
    def _elements(it : tp.Sequence, type_getter : tp.Callable) -> list:
        elements = []
        for elem in it:
            t = type_getter(elem)
            if _issubclass(t, ISABuilder):
                elements.append(tuple(t.enumerate()))
            else:
                elements.append((elem,))

        return elements

class Product(ISABuilder):
    @classmethod
    def enumerate(cls) -> tp.Iterable:
        if not is_dataclass(cls):
            raise TypeError()
        def extract(field):
            t = field.type
            #necesarry as type might be forward declared as a string
            if isinstance(t, str):
                return eval(t)
            else:
                return t
        for args in it.product(*cls._elements(fields(cls), extract)):
            yield cls(*args)

def is_product(product) -> bool:
    return isinstance(product, Product)

def product(cls):
    if not issubclass(cls, Product):
        raise TypeError()
    cls = dataclass(cls)
    return cls

class Enum(ISABuilder, pyEnum):
    @classmethod
    def enumerate(cls) -> tp.Iterable:
        yield from it.chain(*cls._elements(cls, lambda elem : elem.value))

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

class Sum(Enum):
    def __new__(cls, t):
        if not _issubclass(t, ISABuilder):
            raise TypeError()

    @classmethod
    def enumerate(cls) -> tp.Iterable:
        yield from it.chain(*cls._elements(cls, lambda elem : elem.value))

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

def is_sum(sum) -> bool:
    return isinstance(sum, Sum)

new_instruction = auto