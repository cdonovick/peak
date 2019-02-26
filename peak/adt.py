import itertools as it
import typing as tp
from abc import ABCMeta, abstractmethod
from dataclasses import is_dataclass, fields, dataclass, astuple
from enum import auto
from enum import Enum as pyEnum
import weakref

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

    @property
    def value(self):
        return astuple(self)

def is_product(product) -> bool:
    return isinstance(product, Product)

def product(cls):
    if not issubclass(cls, Product):
        raise TypeError()
    cls = dataclass(eq=True, frozen=True)(cls)
    return cls

class Enum(ISABuilder, pyEnum):
    @classmethod
    def enumerate(cls) -> tp.Iterable:
        yield from it.chain(*cls._elements(cls, lambda elem : elem.value))

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

class SumMeta(type):
    _class_cache = weakref.WeakValueDictionary()
    _class_info  = weakref.WeakKeyDictionary()
    def __call__(cls, *args, **kwargs):
        if not cls.is_bound:
            raise TypeError()
        return super().__call__(*args, **kwargs)

    def __new__(mcs, name, bases, namespace, **kwargs):
        bound_types = None
        for base in bases:
            if getattr(base, 'is_bound', False):
                if bound_types is None:
                    bound_types = base.bound_types
                elif bound_types != base.bound_types:
                    raise TypeError("Can't inherit from multiple different bound_types")


        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        SumMeta._class_info[t] = bound_types

        return t

    def __getitem__(cls, idx : tp.Union[tp.Type[ISABuilder], tp.Sequence[tp.Type[ISABuilder]]]) -> 'SumMeta':
        if isinstance(idx, tp.Sequence):
            idx = tuple(idx)
            for t in idx:
                if not _issubclass(t, ISABuilder):
                    raise TypeError()
        elif isinstance(idx, ISABuilder):
            idx = idx,
        else:
            raise TypeError()

        try:
            return SumMeta._class_cache[cls, idx]
        except KeyError:
            pass

        if cls.is_bound:
            raise TypeError()

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, SumMeta))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, idx)
        t = type(cls)(class_name, bases, {})
        t.__module__ = cls.__module__
        SumMeta._class_cache[cls, idx] = t
        SumMeta._class_info[t] = idx
        return t


    @property
    def fields(cls):
        return SumMeta._class_info[cls]

    @property
    def is_bound(cls) -> bool:
        return SumMeta._class_info[cls] is not None

class Sum(ISABuilder, metaclass=SumMeta):
    def __init__(self, value):
        if type(value) not in type(self).fields:
            raise TypeError()
        self._value = value

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.value)

    @property
    def value(self):
        return self._value

    def match(self):
        return type(self.value), self.value

    @classmethod
    def enumerate(cls) -> tp.Iterable:
        for val in it.chain(*cls._elements(cls.fields, lambda elem : elem)):
            yield cls(val)


def is_sum(sum) -> bool:
    return isinstance(sum, Sum)

new_instruction = auto
