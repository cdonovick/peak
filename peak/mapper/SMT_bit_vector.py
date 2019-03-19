import typing as tp
import itertools as it
import functools as ft
import hwtypes as ht

from abc import abstractmethod

import pysmt
import pysmt.shortcuts as smt
from pysmt.typing import  BVType, BOOL

import re
import warnings
import weakref

__ALL__ = ['SMTBitVector', 'SMTNumVector', 'SMTSIntVector', 'SMTUIntVector']

_var_counter = it.count()
_name_table = weakref.WeakValueDictionary()
_free_names = []

def _gen_name():
    if _free_names:
        return _free_names.pop()
    name = f'V_{next(_var_counter)}'
    while name in _name_table:
        name = f'V_{next(_var_counter)}'
    return name

_name_re = re.compile(r'V_\d+')

class _SMYBOLIC:
    def __repr__(self):
        return 'SYMBOLIC'

class _AUTOMATIC:
    def __repr__(self):
        return 'AUTOMATIC'

SMYBOLIC = _SMYBOLIC()
AUTOMATIC = _AUTOMATIC()

def bit_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, other):
        if isinstance(other, SMTBit):
            return fn(self, other)
        else:
            return fn(self, SMTBit(other))
    return wrapped

class SMTBit(ht.AbstractBit):
    @staticmethod
    def get_family() -> ht.TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
        if name is not AUTOMATIC and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')
            _name_table[name] = self
        elif name is AUTOMATIC and value is SMYBOLIC:
            name = _gen_name()
            _name_table[name] = self

        if value is SMYBOLIC:
            self._value = smt.Symbol(name, BOOL)
        elif isinstance(value, pysmt.fnode.FNode):
            if value.get_type().is_bool_type():
                self._value = value
            else:
                raise TypeError(f'Expected bool type not {value.get_type()}')
        elif isinstance(value, SMTBit):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a SMTBit does not cause a new underlying smt variable to be created')
            self._value = value._value
        elif isinstance(value, bool):
            self._value = smt.Bool(value)
        elif isinstance(value, int):
            if value not in {0, 1}:
                raise ValueError('Bit must have value 0 or 1 not {}'.format(value))
            self._value = smt.Bool(bool(value))
        elif hasattr(value, '__bool__'):
            self._value = smt.Bool(bool(value))
        else:
            raise TypeError("Can't coerce {} to Bit".format(type(value)))
        self._name = name

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return self._name
        else:
            return repr(self._value)
    @property
    def value(self):
        return self._value

    @bit_cast
    def __eq__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Iff(self.value, other.value))

    @bit_cast
    def __ne__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Not(smt.Iff(self.value, other.value)))

    def __invert__(self) -> 'SMTBit':
        return type(self)(smt.Not(self.value))

    @bit_cast
    def __and__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.And(self.value, other.value))

    @bit_cast
    def __or__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Or(self.value, other.value))

    @bit_cast
    def __xor__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Xor(self.value, other.value))

    def ite(self, t_branch, f_branch):
        tb_t = type(t_branch)
        fb_t = type(f_branch)
        BV_t = self.get_family().BitVector
        if isinstance(t_branch, BV_t) and isinstance(f_branch, BV_t):
            if tb_t is not fb_t:
                raise TypeError('Both branches must have the same type')
            T = tb_t
        elif isinstance(t_branch, BV_t):
            f_branch = tb_t(f_branch)
            T = tb_t
        elif isinstance(f_branch, BV_t):
            t_branch = fb_t(t_branch)
            T = fb_t
        else:
            t_branch = BV_t(t_branch)
            f_branch = BV_t(f_branch)
            ext = t_branch.size - f_branch.size
            if ext > 0:
                f_branch = f_branch.zext(ext)
            elif ext < 0:
                t_branch = t_branch.zext(-ext)

            T = type(t_branch)


        return T(smt.Ite(self.value, t_branch.value, f_branch.value))

def _coerce(T : tp.Type['SMTBitVector'], val : tp.Any) -> 'SMTBitVector':
    if not isinstance(val, SMTBitVector):
        return T(val)
    elif val.size != T.size:
        raise TypeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['SMTBitVector', 'SMTBitVector'], tp.Any]) -> tp.Callable[['SMTBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self : 'SMTBitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

def int_cast(fn : tp.Callable[['SMTBitVector', int], tp.Any]) -> tp.Callable[['SMTBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self :  'SMTBitVector', other :  tp.Any) -> tp.Any:
        other = int(other)
        return fn(self, other)
    return wrapped

class SMTBitVector(ht.AbstractBitVector):
    @staticmethod
    def get_family() -> ht.TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
        if name is not AUTOMATIC and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')
            _name_table[name] = self
        elif name is AUTOMATIC and value is SMYBOLIC:
            name = _gen_name()
            _name_table[name] = self
        self._name = name

        T = BVType(self.size)

        if value is SMYBOLIC:
            self._value = smt.Symbol(name, T)
        elif isinstance(value, pysmt.fnode.FNode):
            t = value.get_type()
            if t is T:
                self._value = value
            else:
                raise TypeError(f'Expected {T} not {t}')
        elif isinstance(value, SMTBitVector):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a SMTBitVector does not cause a new underlying smt variable to be created')

            ext = self.size - value.size

            if ext < 0:
                warnings.warn('Truncating value from {} to {}'.format(type(value), type(self)))
                self._value = value[:self.size].value
            elif ext > 0:
                self._value = value.zext(ext).value
            else:
                self._value = value.value

        elif isinstance(value, SMTBit):
            self._value = smt.Ite(value.value, smt.BVOne(self.size), smt.BVZero(self.size))

        elif isinstance(value, tp.Sequence):
            if len(value) != self.size:
                raise ValueError('Iterable is not the correct size')
            cls = type(self)
            B1 = cls.unsized_t[1]
            self._value = ft.reduce(cls.concat, map(B1, reversed(value))).value
        elif isinstance(value, int):
            self._value =  smt.BV(value, self.size)

        elif hasattr(value, '__int__'):
            value = int(value)
            self._value = smt.BV(value, self.size)
        else:
            raise TypeError("Can't coerce {} to SMTBitVector".format(type(value)))
        assert self._value.get_type() is T

    def make_constant(self, value, size:tp.Optional[int]=None):
        if size is None:
            size = self.size
        return type(self).unsized_t[size](value)

    @property
    def value(self):
        return self._value

    @property
    def num_bits(self):
        return self.size

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return self._name
        else:
            return repr(self._value)

    def __getitem__(self, index):
        size = self.size
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step

            if start is None:
                start = 0
            elif start < 0:
                start = size + start

            if stop is None:
                stop = size
            elif stop < 0:
                stop = size + stop

            stop = min(stop, size)

            if step is None:
                step = 1
            elif step != 1:
                raise IndexError('SMT extract does not support step != 1')

            v = self.value[start:stop-1]
            return type(self).unsized_t[v.get_type().width](v)
        elif isinstance(index, int):
            if index < 0:
                index = size+index

            if not (0 <= index < size):
                raise IndexError()

            v = self.value[index]
            return self.get_family().Bit(smt.Equals(v, smt.BV(1, 1)))
        else:
            raise TypeError()


    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, SMTBit) or (isinstance(value, int) and value in {0, 1})):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a bit, boolean or 0 or 1, not {value}".format(value=value))

            if index < 0:
                index = self.size+index

            if not (0 <= index < self.size):
                raise IndexError()

            mask = type(self)(1 << index)
            self._value = SMTBit(value).ite(self | mask,  self & ~mask)._value


    def __len__(self):
        return self.size

    @classmethod
    def concat(cls, x, y):
        return cls.unsized_t[x.size + y.size](smt.BVConcat(x.value, y.value))

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

    def adc(self, other : 'SMTBitVector', carry : SMTBit) -> tp.Tuple['BitVector', SMTBit]:
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

    __invert__ = bvnot
    __and__ = bvand
    __or__ = bvor
    __xor__ = bvxor

    __lshift__ = bvshl
    __rshift__ = bvlshr

    __neg__ = bvneg
    __add__ = bvadd
    __sub__ = bvsub
    __mul__ = bvmul
    __floordiv__ = bvudiv
    __mod__ = bvurem

    __eq__ = bveq
    __ne__ = bvne
    __ge__ = bvuge
    __gt__ = bvugt
    __le__ = bvule
    __lt__ = bvult



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

    def __int__(self):
        if self.value.is_constant():
            return self.value.constant_value()
        else:
            raise ValueError("Can't convert symbolic bitvector to int")

    def __bool__(self):
        if self.value.is_constant():
            return bool(self.value.constant_value())
        else:
            raise ValueError("Can't convert symbolic bitvector to bool")


class SMTNumVector(SMTBitVector):
    pass


class SMTUIntVector(SMTNumVector):
    pass

class SMTSIntVector(SMTNumVector):
    def __rshift__(self, other):
        return self.bvashr(other)

    def __floordiv__(self, other):
        return self.bvsdiv(other)

    def __mod__(self, other):
        return self.bvsrem(other)

    def __ge__(self, other):
        return self.bvsge(other)

    def __gt__(self, other):
        return self.bvsgt(other)

    def __lt__(self, other):
        return self.bvslt(other)

    def __le__(self, other):
        return self.bvsle(other)

_Family_ = ht.TypeFamily(SMTBit, SMTBitVector, SMTUIntVector, SMTSIntVector)
