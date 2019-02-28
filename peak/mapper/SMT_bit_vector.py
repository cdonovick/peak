import typing as tp
import itertools as it
import functools as ft
import smt_switch as ss
import hwtypes as bv
from abc import abstractmethod
import re
import warnings
import weakref

__ALL__ = ['SMTBitVector', 'SMTNumVector', 'SMTSIntVector', 'SMTUIntVector']

_var_counter = it.count()
_name_table = weakref.WeakValueDictionary()

def _gen_name():
    name = f'V_{next(_var_counter)}'
    while name in _name_table:
        name = f'V_{next(_var_counter)}'
    return name

_name_re = re.compile(r'V_\d+')

def auto_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, *args):
        T = type(self)
        def cast(x):
            if isinstance(x, T):
                return x
            else:
                return T(x)
        args = map(cast, args)
        return cast(fn(self, *args))
    return wrapped

def auto_cast_bool(fn):
    @ft.wraps(fn)
    def wrapped(self, *args):
        solver = self.solver
        T = type(self)
        def cast(x):
            if isinstance(x, T):
                return x
            else:
                return T(x)
        args = map(cast, args)
        r = fn(self, *args)
        bit = solver.BitVec(1)
        r = solver.Ite(r, solver.TheoryConst(bit, 1), solver.TheoryConst(bit, 0))
        return T.unsized_t[1](r)
    return wrapped

class SMTBitVector(bv.AbstractBitVector):
    @abstractmethod
    def __init__(self, solver:ss.smt, value:tp.Union[None, bool, int, bv.BitVector, ss.terms.TermBase] = None,  *, name:tp.Optional[str] = None):
        self._solver = solver

        if name is not None:
            if name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')

        if value is None:
            self._sort = sort = solver.BitVec(self.size)
            if name is None:
                name = _gen_name()
            self._value = solver.DeclareConst(name, sort)
            self._const_value = None

        elif isinstance(value, SMTBitVector):
            self._value = value.value
            if value.size != self.size:
                raise TypeError("inconsistent bitwidth")
            self._sort = value._sort
            if name is None:
                name = value._name
            else:
                warnings.warn('Changing the name of a SMTBitVector does not cause a new underlying smt variable to be created')
            self._const_value = value._const_value

        elif isinstance(value, ss.terms.TermBase):
            #Value is a smt expression
            if isinstance(value.sort, ss.sorts.Bool) and self.size != 1:
                raise TypeError("inconsistent bitwidth")
            elif isinstance(value.sort, ss.sorts.BitVec) and value.sort.width != self.size:
                raise TypeError("inconsistent bitwidth")

            self._sort = value.sort
            self._value  = value
            self._const_value = None
        else:
            if isinstance(value, bool):
                value = int(value)
            elif isinstance(value, bv.BitVector):
                value = value.as_uint()
            elif not isinstance(value, int):
                raise TypeError(f'Unexpected type {type(value)}')
            self._sort = sort = solver.BitVec(self.size)
            self._const_value = value
            self._value = solver.TheoryConst(sort, value)

        self._name = name
        if name is not None:
            _name_table[name] = self

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

    @property
    def solver(self):
        return self._solver

    def __repr__(self):
        if self._name is not None:
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

            v = self.value[stop-1 : start]
        else:
            if index < 0:
                index = size+index

            if not (0 <= index < size):
                raise IndexError()

            v = self.value[index]

        return type(self).unsized_t[v.sort.width](v)

    def __setitem__(self, index, value):
        #not sure what a set item should mean
        raise NotImplementedError()

    def __len__(self):
        return self.num_bits

    @classmethod
    def concat(cls, x, y):
        if isinstance(x, SMTBitVector) and isinstance(y, SMTBitVector):
            if x.solver is not y.solver:
                raise ValueError('x and y bound to different solvers')
            solver = x.solver
        elif isinstance(x, SMTBitVector):
            solver = x.solver
            y = SMTBitVector(solver, y)
        elif isinstance(y, SMTBitVector):
            solver = y.solver
            x = SMTBitVector(solver, x)
        else:
            raise ValueError('x or y must be an SMTBitVector')
        return cls.unsized_t[x.size + y.size](solver.Concat(x.value, y.value))

    @auto_cast
    def bvnot(self):
        return self.solver.BVNot(self.value)

    @auto_cast
    def bvand(self, other):
        return self.solver.BVAnd(self.value, other.value)

    @auto_cast
    def bvnand(self, other):
        return self.solver.BVNot(self.bvand(other))

    @auto_cast
    def bvor(self, other):
        return self.solver.BVOr(self.value, other.value)

    @auto_cast
    def bvnor(self, other):
        return self.solver.BVNot(self.bvor(other))

    @auto_cast
    def bvxor(self, other):
        return self.solver.BVXor(self.value, other.value)

    @auto_cast
    def bvxnor(self, other):
        return self.solver.BVNot(self.bvxor(other))

    @auto_cast
    def bvshl(self, other):
        return self.solver.BVShl(self.value, other.value)

    @auto_cast
    def bvlshr(self, other):
        return self.solver.BVLshr(self.value, other.value)

    @auto_cast
    def bvashr(self, other):
        return self.solver.BVAshr(self.value, other.value)

    def bvrol(self, other):
        raise NotImplementedError()

    def bvror(self, other):
        raise NotImplementedError()

    @auto_cast_bool
    def bvcomp(self, other):
        return self.solver.Equals(self.value, other.value)

    bveq = bvcomp

    @auto_cast_bool
    def bvne(self, other):
        return self.solver.Not(self.solver.Equals(self.value, other.value))

    @auto_cast_bool
    def bvult(self, other):
        return self.solver.BVUlt(self.value, other.value)

    @auto_cast_bool
    def bvule(self, other):
        return self.solver.BVUle(self.value, other.value)

    @auto_cast_bool
    def bvugt(self, other):
        return self.solver.BVUgt(self.value, other.value)

    @auto_cast_bool
    def bvuge(self, other):
        return self.solver.BVUge(self.value, other.value)

    @auto_cast_bool
    def bvslt(self, other):
        return self.solver.BVSlt(self.value, other.value)

    @auto_cast_bool
    def bvsle(self, other):
        return self.solver.BVSle(self.value, other.value)

    @auto_cast_bool
    def bvsgt(self, other):
        return self.solver.BVSgt(self.value, other.value)

    @auto_cast_bool
    def bvsge(self, other):
        return self.solver.BVSge(self.value, other.value)

    @auto_cast
    def bvneg(self):
        return self.solver.BVNeg(self.value)

    def adc(self, b, c):
        T = type(self)
        if not isinstance(b, T):
            b = T(b)

        if not isinstance(c, T.unsized_t[1]):
            c = T.unsized_t[1](c)

        if c.num_bits != 1:
            warnings.warn('carry is not single bit something weird might happen')

        a = self.zext(1)
        b = b.zext(1)
        c = c.zext(1+self.size-c.size)
        res = a + b + c
        return res[0:-1], res[-1]

    def ite(self, t, e):
        T = type(self).unsized_t
        if not isinstance(t, T) and not isinstance(e, T):
            t = int(t)
            e = int(e)
            size = max(t.bit_length(), e.bit_length())
            TS = type(self).unsized_t[size]
            t = T(e)
            e = T(e)
        elif not isinstance(t, T):
            TS = type(e)
            t =  T(t)
        elif not isinstance(e, T):
            TS = type(t)
            e = T(e)
        else:
            if t.size != e.size:
                raise TypeError()
            TS = type(t)
        return TS(self.solver.Ite(self.value != self.make_constant(0).value, t.value, e.value))

    @auto_cast
    def bvadd(self, other):
        return self.solver.BVAdd(self.value, other.value)

    @auto_cast
    def bvsub(self, other):
        return self.solver.BVSub(self.value, other.value)

    @auto_cast
    def bvmul(self, other):
        return self.solver.BVMul(self.value, other.value)

    @auto_cast
    def bvudiv(self, other):
        return self.solver.BVUdiv(self.value, other.value)

    @auto_cast
    def bvurem(self, other):
        return self.solver.BVUrem(self.value, other.value)

    @auto_cast
    def bvsdiv(self, other):
        # currently not in smt switch
        raise NotImplementedError()
        return self.solver.BVSdiv(self.value, other.value)

    @auto_cast
    def bvsrem(self, other):
        raise NotImplementedError()
        return self.solver.BVSrem(self.value, other.value)

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

    def is_x(self):
        raise NotImplementedError()

    def as_uint(self):
        raise NotImplementedError()

    def as_sint(self):
        raise NotImplementedError()

    as_int = as_sint

    #def __int__(self):
    #    raise NotImplementedError()

    #def __bool__(self):
    #    raise NotImplementedError()

    def binary_string(self):
        raise NotImplementedError()

    def as_binary_string(self):
        raise NotImplementedError()

    def bits(self):
        raise NotImplementedError()

    def as_bool_list(self):
        raise NotImplementedError()

    def repeat(self, other):
        raise NotImplementedError()

    def sext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.

        The user is responsible for handling the conversion. This behavior was
        chosen due to issues with subclassing BitVector (e.g. Bits(n) type
        generator which specializes num_bits). Basically, it's not guaranteed
        that a subtype will respect the __init__ interface, so we return a raw
        BitVector instead and require the user to correctly convert back to the
        subtype.

        Subtypes can improve ergonomics by implementing their own extension
        operators which handle the implicit conversion from raw BitVector.

        TODO: Do this implicit conversion for built-in types like UIntVector.
        """
        T = type(self).unsized_t
        ext = int(other)
        if ext < 0:
            raise ValueError()
        elif ext == 0:
            return self
        else:
            x = self[self.num_bits - 1]
            XT = type(x).unsized_t
            for i in range(1, ext):
                x = XT.concat(x, x)
        return T.concat(x, self)

    def ext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.  See
        docstring for `sext` for more info.
        """
        return self.zext(other)

    def zext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.  See
        docstring for `sext` for more info.
        """
        T = type(self).unsized_t
        ext = int(other)
        if ext < 0:
            raise ValueError()
        elif ext == 0:
            return self

        return T.concat(T[ext](0), self)


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

def bind_solver(T : tp.Type[SMTBitVector], solver) -> tp.Type[SMTBitVector]:
    class BoundVector(T):
        def __init__(self, *args, **kwargs):
            super().__init__(solver, *args, **kwargs)
    return BoundVector

def overflow(a, b, res):
   raise NotImplementedError()

