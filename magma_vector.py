import magma as m
from hwtypes import  AbstractBitVector, AbstractBit, TypeFamily, InconsistentSizeError
from hwtypes import build_ite
import functools as ft

class MagmaBitMeta(m.MagmaProtocolMeta):
    _class_cache = weakref.WeakValueDictionary()

    def __new__(cls, name, bases, namespace, info=(None, None), **kwargs):
        # TODO: A lot of this code is shared with AbstractBitVectorMeta, we
        # should refactor to reuse
        if '_info_' in namespace:
            raise TypeError(
                'class attribute _info_ is reversed by the type machinery')

        direction = info[1]
        for base in bases:
            if getattr(base, 'is_directed', False):
                if direction is None:
                    direction = base.direction
                elif direction != base.direction:
                    raise TypeError(
                        "Can't inherit from multiple different directions")

        namespace['_info_'] = info[0], direction
        type_ = super().__new__(cls, name, bases, namespace, **kwargs)
        if direction is None:
            # class is unundirected so t.unundirected_t -> t
            type_._info_ = type_, direction
        elif info[0] is None:
            # class inherited from directed types so there is no unundirected_t
            type_._info_ = None, direction

        return type_

    def __getitem__(cls, direction: Direction) -> 'DigitalMeta':
        mcs = type(cls)
        try:
            return mcs._class_cache[cls, direction]
        except KeyError:
            pass

        if not isinstance(direction, Direction):
            raise TypeError('Direction of Digital must be an instance of '
                            'm.Direction')

        if cls.is_directed:
            if direction == direction.Undirected:
                return cls.undirected_t
            if direction == cls.direction:
                return cls
            else:
                return cls.undirected_t[direction]
        if direction == direction.Undirected:
            return cls

        bases = [cls]
        bases.extend(b[direction] for b in cls.__bases__ if isinstance(b, mcs))
        bases = tuple(bases)
        orig_name = cls.__name__
        class_name = '{}[{}]'.format(orig_name, direction.name)
        type_ = mcs(class_name, bases, {},
                    info=(cls, direction))
        type_.__module__ = cls.__module__
        mcs._class_cache[cls, direction] = type_
        return type_




    @property
    def undirected_t(cls) -> 'DigitalMeta':
        t = cls._info_[0]
        if t is not None:
            return t
        else:
            raise AttributeError('type {} has no undirected_t'.format(cls))

    def _to_magma_(cls): 
        return m.Bit.qualify(cls._info_[1])

    def _qualify_magma_(cls, d): 
        return cls.undirected_t[d]


    def _flip_magma_(cls): 
        ###BOOKMARK###
        d = cls.[3]
        if d == m.Direction.In:
            return cls.undirected_t[m.Direction.Out]
        elif d == m.Direction.Out:
            return cls.undirected_t[m.Direction.In]
        else:
            return cls

    def _from_magma_value_(cls, value):
        d = cls.fields[3]
        if d == m.Direction.In:
            return cls.undirected_t[(*cls.fields[:-1], m.Direction.Out)]
        elif d == m.Direction.Out:
            return cls.undirected_t[(*cls.fields[:-1], m.Direction.In)]
        else:
            return cls


def bit_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, other):
        if isinstance(other, MagmaBit):
            return fn(self, other)
        else:
            try:
                other = MagmaBit(other)
            except TypeError:
                return NotImplemented
            return fn(self, other)
    return wrapped

class MagmaBit(AbstractBit):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, *args, **kwargs):
        self._value=m.Bit(*args, **kwargs)

    def __repr__(self):
        return self._value.__repr__()

    @property
    def value(self):
        return self._value

    @bit_cast
    def __eq__(self, other : 'MagmaBit') -> 'MagmaBit':
        return type(self)(self.value.__eq__(other.value))

    @bit_cast
    def __ne__(self, other : 'MagmaBit') -> 'MagmaBit':
        return type(self)(self.value.__ne__(other.value))

    def __invert__(self) -> 'MagmaBit':
        return type(self)(self.value.__invert__())

    @bit_cast
    def __and__(self, other : 'MagmaBit') -> 'MagmaBit':
        return type(self)(self.value.__and__(other.value))

    @bit_cast
    def __or__(self, other : 'MagmaBit') -> 'MagmaBit':
        return type(self)(self.value.__or__(other.value))

    @bit_cast
    def __xor__(self, other : 'MagmaBit') -> 'MagmaBit':
        return type(self)(self.value.__xor__(other.value))

    def ite(self, t_branch, f_branch):
        return type(self)(self.value.ite(t_branch, f_branch))

#         def _ite(select, t_branch, f_branch):
#             return smt.Ite(select.value, t_branch.value, f_branch.value)
#         return build_ite(_ite, self, t_branch, f_branch)

    def __bool__(self):
        raise TypeError('MagmaBit cannot be converted to bool')


