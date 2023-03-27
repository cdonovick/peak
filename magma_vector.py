import magma as m
from hwtypes import  AbstractBitVector, AbstractBit, TypeFamily, InconsistentSizeError
from hwtypes import build_ite
import functools as ft
import typing as tp

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

    def __getitem__(cls, direction: Direction) -> 'MagmaBitMeta':
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
    def undirected_t(cls) -> 'MagmaBitMeta':
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
        d = cls._info_[1]
        if d == m.Direction.In:
            return cls.undirected_t[m.Direction.Out]
        elif d == m.Direction.Out:
            return cls.undirected_t[m.Direction.In]
        else:
            return cls

    def _from_magma_value_(cls, value):
        if not value.is_oriented(cls._info_[1]):
            raise TypeError('value is not properly oriented')
        return cls(value)

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

class MagmaBit(AbstractBit, m.MagmaProtocol, metaclass=MagmaBitMeta):
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

# class AbstractBitVectorMeta(type): #:(ABCMeta):
class MagmaVectorMeta(AbstractBitVectorMeta, m.MagmaProtocolMeta): #:(ABCMeta):
    # BitVectorType, size :  BitVectorType[size]
    # _class_cache = weakref.WeakValueDictionary()

    def __new__(mcs, name, bases, namespace, info=(None, None, None), **kwargs):

        direction = info[2]
        for base in bases:
            if getattr(base, 'is_directed', False):
                if direction is None:
                    direction = base.direction
                elif direction != base.direction:
                    raise TypeError(
                        "Can't inherit from multiple different directions")

        t = super().__new__(mcs, name, bases, namespace, info[:2], **kwargs)
        t._info_ = *t._info_, direction
        return t


    # def __getitem__(cls, idx : tp.Tuple[int, m.Direction]) -> 'MagmaVectorMeta':
    def __getitem__(cls, idx : tp.Union[int, tp.Tuple[int, m.Direction]]) -> 'MagmaVectorMeta':
        mcs = type(cls)
        try:
            return mcs._class_cache[cls, idx]
        except KeyError:
            pass

        if isinstance(idx, int):
            size, direction = idx, m.Direction.Undirected
        elif isinstance(idx, tuple):
            if len(idx) != 2:
                raise TypeError('Expected (size,direction) tuple')
            size, direction = idx
        else:
            raise TypeError('BitVectors must be bound to int, [Direction]')
            
        if size < 0:
            raise ValueError('Size of BitVectors must be positive')

        if cls.is_sized:
            raise TypeError('{} is already sized'.format(cls))

        idx = size, direction

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, mcs))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, idx)
        t = mcs(class_name, bases, {}, info=(cls,idx))
        t.__module__ = cls.__module__
        mcs._class_cache[cls, idx] = t
        return t

    @property
    def unbound_t(cls) -> 'MagmaVectorMeta':
        t = cls._info_[0]
        if t is not None:
            return t
        else:
            raise AttributeError('type {} has no unbound_t'.format(cls))

    @property
    def size(cls) -> int:
        return cls._info_[1]

    @property
    def is_sized(cls) -> bool:
        return cls.size is not None

    def __len__(cls):
        if cls.is_sized:
            return cls.size
        else:
            raise AttributeError('unsized type has no len')

    def __repr__(cls):
        return cls.__name__

    def _to_magma_(cls): 
        return m.Bits[cls.size].qualify(cls._info_[2])

    def _qualify_magma_(cls, d): 
        return cls.unbound_t[cls.size,d]

    def _flip_magma_(cls):
        d = cls._info_[2]
        if d == m.Direction.In:
            return cls.unbound_t[cls.size, m.Direction.Out]
        elif d == m.Direction.Out:
            return cls.unbound_t[cls.size, m.Direction.In]
        else:
            return cls

    def _from_magma_value_(cls, value):
        if not value.is_oriented(cls._info_[2]):
            raise TypeError('value is not properly oriented')
        return cls(value)

# END class MagmaVectorMeta


# BEGIN PASTE-IN from hwtypes_leonardt/hwtypes/smt_bit_vector.py

def _coerce(T : tp.Type['MagmaBitVector'], val : tp.Any) -> 'MagmaBitVector':
    if not isinstance(val, MagmaBitVector):
        return T(val)
    elif val.size != T.size:
        raise InconsistentSizeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['MagmaBitVector', 'MagmaBitVector'], tp.Any]) -> tp.Callable[['MagmaBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self : 'MagmaBitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

def int_cast(fn : tp.Callable[['MagmaBitVector', int], tp.Any]) -> tp.Callable[['MagmaBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self :  'MagmaBitVector', other :  tp.Any) -> tp.Any:
        other = int(other)
        return fn(self, other)
    return wrapped

class MagmaBitVector(AbstractBitVector):

#     @staticmethod
#     def get_family() -> TypeFamily:
#         return _Family_
# 
    def __init__(self, *args, **kwargs):
        cls = type(self)
        self._value = cls._to_magma_(*args, **kwargs)

    def make_constant(self, value):
        return type(self)(value)

    @property
    def num_bits(self):
        return self.size

    def __repr__(self):
        return self._value.__repr__()

    def __getitem__(self, index):
        v = self._value.__getitem__(index)

        if isinstance(v, m.Bit):
            return MagmaBit(v)
        else:
            cls = type(self)
            return cls.unbound_t[v.size](v)

    def __len__(self):
        return self.size

    def concat(self, other):
        T = type(self).unsized_t
        if not isinstance(other, T):
            raise TypeError(f'value must of type {T} not {type(other)}')
        return T[self.size + other.size](smt.BVConcat(other.value, self.value))

    def bvnot(self):
        return type(self)(smt.BVNot(self.value))

    @bv_cast
    def bvand(self, other):
        return type(self)(smt.BVAnd(self.value, other.value))

    @bv_cast
    def bvnand(self, other):
        return type(self)(smt.BVNot(smt.BVAnd(self.value, other.value)))

    @bv_cast
    def bvor(self, other):
        return type(self)(smt.BVOr(self.value, other.value))

    @bv_cast
    def bvnor(self, other):
        return type(self)(smt.BVNot(smt.BVOr(self.value, other.value)))

    @bv_cast
    def bvxor(self, other):
        return type(self)(smt.BVXor(self.value, other.value))

    @bv_cast
    def bvxnor(self, other):
        return type(self)(smt.BVNot(smt.BVXor(self.value, other.value)))

    @bv_cast
    def bvshl(self, other):
        return type(self)(smt.BVLShl(self.value, other.value))

    @bv_cast
    def bvlshr(self, other):
        return type(self)(smt.BVLShr(self.value, other.value))

    @bv_cast
    def bvashr(self, other):
        return type(self)(smt.BVAShr(self.value, other.value))

    @int_cast
    def bvrol(self, other):
        return type(self)(smt.get_env().formula_manager.BVRol(self.value, other))

    @int_cast
    def bvror(self, other):
        return type(self)(smt.get_env().formula_manager.BVRor(self.value, other))

    @bv_cast
    def bvcomp(self, other):
        return type(self).unsized_t[1](smt.BVComp(self.value, other.value))

    @bv_cast
    def bveq(self,  other):
        return self.get_family().Bit(smt.Equals(self.value, other.value))

    @bv_cast
    def bvne(self, other):
        return self.get_family().Bit(smt.NotEquals(self.value, other.value))

    @bv_cast
    def bvult(self, other):
        return self.get_family().Bit(smt.BVULT(self.value, other.value))

    @bv_cast
    def bvule(self, other):
        return self.get_family().Bit(smt.BVULE(self.value, other.value))

    @bv_cast
    def bvugt(self, other):
        return self.get_family().Bit(smt.BVUGT(self.value, other.value))

    @bv_cast
    def bvuge(self, other):
        return self.get_family().Bit(smt.BVUGE(self.value, other.value))

    @bv_cast
    def bvslt(self, other):
        return self.get_family().Bit(smt.BVSLT(self.value, other.value))

    @bv_cast
    def bvsle(self, other):
        return self.get_family().Bit(smt.BVSLE(self.value, other.value))

    @bv_cast
    def bvsgt(self, other):
        return self.get_family().Bit(smt.BVSGT(self.value, other.value))

    @bv_cast
    def bvsge(self, other):
        return self.get_family().Bit(smt.BVSGE(self.value, other.value))

    def bvneg(self):
        return type(self)(smt.BVNeg(self.value))

    def adc(self, other : 'MagmaBitVector', carry : SMTBit) -> tp.Tuple['BitVector', SMTBit]:
        """
        add with carry

        returns a two element tuple of the form (result, carry)

        """
        T = type(self)
        other = _coerce(T, other)
        carry = _coerce(T.unsized_t[1], carry)

        a = self.zext(1)
        b = other.zext(1)
        c = carry.zext(T.size)

        res = a + b + c
        return res[0:-1], res[-1]

    def ite(self, t_branch, f_branch):
        return self.bvne(0).ite(t_branch, f_branch)

    @bv_cast
    def bvadd(self, other):
        return type(self)(smt.BVAdd(self.value, other.value))

    @bv_cast
    def bvsub(self, other):
        return type(self)(smt.BVSub(self.value, other.value))

    @bv_cast
    def bvmul(self, other):
        return type(self)(smt.BVMul(self.value, other.value))

    @bv_cast
    def bvudiv(self, other):
        return type(self)(smt.BVUDiv(self.value, other.value))

    @bv_cast
    def bvurem(self, other):
        return type(self)(smt.BVURem(self.value, other.value))

    @bv_cast
    def bvsdiv(self, other):
        return type(self)(smt.BVSDiv(self.value, other.value))

    @bv_cast
    def bvsrem(self, other):
        return type(self)(smt.BVSRem(self.value, other.value))

    def __invert__(self): return self.bvnot()

    def __and__(self, other):
        try:
            return self.bvand(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __or__(self, other):
        try:
            return self.bvor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __xor__(self, other):
        try:
            return self.bvxor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __lshift__(self, other):
        try:
            return self.bvshl(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __rshift__(self, other):
        try:
            return self.bvlshr(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __neg__(self): return self.bvneg()

    def __add__(self, other):
        try:
            return self.bvadd(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __sub__(self, other):
        try:
            return self.bvsub(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mul__(self, other):
        try:
            return self.bvmul(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.bvudiv(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        try:
            return self.bvurem(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __eq__(self, other):
        try:
            return self.bveq(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.bvne(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.bvuge(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.bvugt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.bvule(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.bvult(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError as e:
            return NotImplemented


    @int_cast
    def repeat(self, other):
        return type(self)(smt.get_env().formula_manager.BVRepeat(self.value, other))

    @int_cast
    def sext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](smt.BVSExt(self.value, ext))

    def ext(self, ext):
        return self.zext(ext)

    @int_cast
    def zext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](smt.BVZExt(self.value, ext))

# END PASTE-UP from hwtypes_leonardt/hwtypes/smt_bit_vector.py

# class AbstractBitVector(metaclass=MagmaVectorMeta):
#     @staticmethod
#     def get_family() -> TypeFamily:
#         return _Family_
# 
#     @property
#     def size(self) -> int:
#         return  type(self).size
# 
#     @classmethod
#     @abstractmethod
#     def make_constant(self, value, num_bits:tp.Optional[int]=None) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def __getitem__(self, index) -> AbstractBit:
#         pass
# 
#     @abstractmethod
#     def __setitem__(self, index : int, value : AbstractBit):
#         pass
# 
#     @abstractmethod
#     def __len__(self) -> int:
#         pass
# 
#     @abstractmethod
#     def concat(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvnot(self) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvand(self, other) -> 'AbstractBitVector':
#         pass
# 
#     def bvnand(self, other) -> 'AbstractBitVector':
#         return self.bvand(other).bvnot()
# 
#     @abstractmethod
#     def bvor(self, other) -> 'AbstractBitVector':
#         pass
# 
#     def bvnor(self, other) -> 'AbstractBitVector':
#         return self.bvor(other).bvnot()
# 
#     @abstractmethod
#     def bvxor(self, other) -> 'AbstractBitVector':
#         pass
# 
#     def bvxnor(self, other) -> 'AbstractBitVector':
#         return self.bvxor(other).bvnot()
# 
#     @abstractmethod
#     def bvshl(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvlshr(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvashr(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvrol(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvror(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvcomp(self, other) -> 'AbstractBitVector[1]':
#         pass
# 
#     @abstractmethod
#     def bveq(self, other) -> AbstractBit:
#         pass
# 
#     def bvne(self, other) -> AbstractBit:
#         return ~self.bveq(other)
# 
#     @abstractmethod
#     def bvult(self, other) -> AbstractBit:
#         pass
# 
#     def bvule(self, other) -> AbstractBit:
#         return self.bvult(other) | self.bveq(other)
# 
#     def bvugt(self, other) -> AbstractBit:
#         return ~self.bvule(other)
# 
#     def bvuge(self, other) -> AbstractBit:
#         return ~self.bvult(other)
# 
#     @abstractmethod
#     def bvslt(self, other) -> AbstractBit:
#         pass
# 
#     def bvsle(self, other) -> AbstractBit:
#         return self.bvslt(other) | self.bveq(other)
# 
#     def bvsgt(self, other) -> AbstractBit:
#         return ~self.bvsle(other)
# 
#     def bvsge(self, other) -> AbstractBit:
#         return ~self.bvslt(other)
# 
#     @abstractmethod
#     def bvneg(self) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def adc(self, other, carry) -> tp.Tuple['AbstractBitVector', AbstractBit]:
#         pass
# 
#     @abstractmethod
#     def ite(i,t,e) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvadd(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvsub(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvmul(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvudiv(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvurem(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvsdiv(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def bvsrem(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def repeat(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def sext(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def ext(self, other) -> 'AbstractBitVector':
#         pass
# 
#     @abstractmethod
#     def zext(self, other) -> 'AbstractBitVector':
#         pass
# 
