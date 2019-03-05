import itertools as it
import typing as tp
from hwtypes import AbstractBitVector, AbstractBit
from abc import ABCMeta, abstractmethod
from enum import auto as new_instruction
from enum import Enum as pyEnum
from enum import EnumMeta as pyEnumMeta
import weakref
import dataclasses as dc

__all__ =  ['new', 'ISABuilder', 'Product', 'is_product', 'Tuple', ]
__all__ += ['Sum', 'is_sum',]
__all__ += ['Enum', 'is_enum', 'new_instruction']


def new(klass, bind=None):
    class T(klass): pass
    if bind is not None:
        return T[bind]
    else:
        return T

def _issubclass(sub : tp.Any, parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

def _field_type(field : dc.Field) -> type:
    t = field.type
    #necesarry as type might be forward declared as a string
    if isinstance(t, str):
        return eval(t)
    else:
        return t

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

_CONSTANT_TYPES = (bool, AbstractBit, int, AbstractBitVector)
_FIELD_TYPES = ISABuilder, *_CONSTANT_TYPES

class ProductMeta(type):
    def __call__(cls, *value):
        for v,t in zip(value, cls.fields):
            if not isinstance(v, t):
                raise TypeError('Value {} is not of type {}'.format(v, t))
        return super().__call__(*value)

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls = dc.dataclass(eq=True, frozen=True)(cls)
        _fields = []
        for field in dc.fields(cls):
            t = _field_type(field)
            if field.default is not dc.MISSING and not isinstance(field.default, t):
                raise TypeError()
            elif field.default_factory is not dc.MISSING:
                raise ValueError('fields should not define default factory')
            if not _issubclass(t, _FIELD_TYPES) and not isinstance(t, _FIELD_TYPES):
                raise TypeError('Unsupported Field type: {}'.format(t))
            _fields.append(t)

        cls._fields = tuple(_fields)
        return cls

    @property
    def fields(cls):
        return cls._fields


class Product(ISABuilder, metaclass=ProductMeta):
    @classmethod
    def enumerate(cls) -> tp.Iterable:
        for args in it.product(*cls._elements(dc.fields(cls), _field_type)):
            yield cls(*args)

    @property
    def value(self):
        return dc.astuple(self)

def is_product(product) -> bool:
    return isinstance(product, Product)

class BoundMeta(type):
    _class_cache = weakref.WeakValueDictionary()
    _class_info  = weakref.WeakKeyDictionary()
    def __call__(cls, *args, **kwargs):
        if not cls.is_bound:
            obj = cls.__new__(cls, *args, **kwargs)
            if not type(obj).is_bound:
                raise TypeError('Cannot instance unbound type')
            if isinstance(obj, cls):
                obj.__init__(*args, **kwargs)
            return obj
        return super().__call__(*args, **kwargs)

    def __new__(mcs, name, bases, namespace, **kwargs):
        bound_types = None
        for base in bases:
            if isinstance(base, BoundMeta) and base.is_bound:
                if bound_types is None:
                    bound_types = base.fields
                elif bound_types != base.fields:
                    raise TypeError("Can't inherit from multiple different bound_types")


        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        BoundMeta._class_info[t] = bound_types

        return t

    def __getitem__(cls, idx : tp.Union[tp.Type[ISABuilder], tp.Sequence[tp.Type[ISABuilder]]]) -> 'BoundMeta':
        if isinstance(idx, tp.Iterable):
            idx = tuple(idx)
            for t in idx:
                if not _issubclass(t, _FIELD_TYPES):
                    raise TypeError(t)
        elif isinstance(idx, ISABuilder):
            idx = idx,
        else:
            raise TypeError(idx)

        try:
            return BoundMeta._class_cache[cls, idx]
        except KeyError:
            pass

        if cls.is_bound:
            raise TypeError('Type is already bound')

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, BoundMeta))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, idx)
        t = type(cls)(class_name, bases, {})
        t.__module__ = cls.__module__
        BoundMeta._class_cache[cls, idx] = t
        BoundMeta._class_info[t] = idx
        return t


    @property
    def fields(cls):
        return BoundMeta._class_info[cls]

    @property
    def is_bound(cls) -> bool:
        return BoundMeta._class_info[cls] is not None

class Sum(ISABuilder, metaclass=BoundMeta):
    def __init__(self, value):
        if type(value) not in type(self).fields:
            raise TypeError('Value {} is not of types {}'.format(value, type(self).fields))
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

#basically an anonymous product
class Tuple(ISABuilder, metaclass=BoundMeta):
    def __new__(cls, *value):
        if cls.is_bound:
            return super().__new__(cls)
        else:
            idx = tuple(type(v) for v in value)
            return cls[idx].__new__(cls[idx], *value)

    def __init__(self, *value):
        cls = type(self)
        if len(value) != len(cls.fields):
            raise ValueError('Incorrect number of arguments')
        for v,t in zip(value, cls.fields):
            if not isinstance(v,t):
                raise TypeError('Value {} is not of type {}'.format(v, t))

        self._value = value

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.value)

    def __getitem__(self, idx):
        return self.value[idx]

    @property
    def value(self):
        return self._value

    @classmethod
    def enumerate(cls) -> tp.Iterable:
        for args in it.product(*cls._elements(cls.fields, lambda x : x)):
            yield cls(*args)

class Enum(ISABuilder, pyEnum):
    def __new__(cls, *value):
        if not all(isinstance(v, (new_instruction, *_CONSTANT_TYPES)) for v in value):
            raise TypeError('Enum values must be int or BitVector')
        obj = object.__new__(cls)
        if len(value) == 1:
            obj._value_ = value[0]
        else:
            obj._value_ = value

        return obj

    @classmethod
    def enumerate(cls) -> tp.Iterable:
        yield from it.chain(*cls._elements(cls, lambda elem : elem.value))

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

def is_enum(enum) -> bool:
    return isinstance(enum, Enum)

