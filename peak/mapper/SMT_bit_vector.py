import typing as tp
import itertools as it
import functools as ft
import smt_switch as ss
import bit_vector as bv

_var_counter = it.count()

def auto_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, *args):
        T = type(self)
        solver = self._solver
        num_bits = self._num_bits
        def cast(x):
            if isinstance(x, T):
                return x
            else:
                return T(solver, x, num_bits)
        args = map(cast, args)
        return cast(fn(self, *args))
    return wrapped

def auto_cast_bool(fn):
    @ft.wraps(fn)
    def wrapped(self, *args):
        T = type(self)
        solver = self._solver
        num_bits = self._num_bits
        def cast(x):
            if isinstance(x, T):
                return x
            else:
                return T(solver, x, num_bits)
        args = map(cast, args)
        r = fn(self, *args)
        bit = solver.BitVec(1)
        r = solver.Ite(r, solver.TheoryConst(1, bit), solver.TheoryConst(0, bit))
        return SMTBitVector(solver, r, 1)
    return wrapped

class SMTBitVector:
    def __init__(self, solver:ss.smt, value:tp.Union[None, bool, int, bv.BitVector, ss.src.TermBase] = None, num_bits:tp.Optional[Int]=None):
        self._solver = solver

        if value is None and num_bits is None:
            raise ValueError("Must supply either value or num_bits")
        elif value is None:
            self._num_bits = num_bits
            self._sort = sort = solver.BitVec(num_bits)
            self._name = name = f'V_{next(_var_counter)}'
            self._value = value = solver.DeclareConst(name, sort)
        elif isinstance(value, ss.terms.TermBase):
            #Value is a smt expression
            if isinstance(value.sort, ss.sorts.Bool):
                self._num_bits =  1
            elif isinstance(value.sort, ss.sorts.BitVec)
                self._num_bits = value.sort.width
            else:
                raise TypeError()
            self._sort = value.sort
            self._name = f'E_{value}'
            self._value  = value
        else:
            if isinstance(value, bool):
                if num_bits is None:
                    num_bits = 1
                value = int(value)
            elif isinstance(value, int):
                if num_bits is None:
                    num_bits = max(1, value.bit_length())
            elif isinstance(value, bv.BitVector):
                if num_bits is None:
                    num_bits = value.num_bits
                value = value.as_uint()
            else:
                raise TypeError()
            self._num_bits = num_bits
            self._sort = sort = solver.BitVec(num_bits)
            self._name = f"C_{num_bits}'d{value}"
            self._value = value = solver.TheoryConst(sort, value)

    @property
    def value(self):
        return self._value

    @auto_cast
    def bvnot(self):
        return self._solver.BVNot(self.value)

    @auto_cast
    def bvand(self, other):
        return self._solver.BVAnd(self.value, other.value)

    @auto_cast
    def bvnand(self, other):
        return self.bvand(other).bvnot()

    @auto_cast
    def bvor(self, other):
        return self._solver.BVOr(self.value, other.value)

    @auto_cast
    def bvnor(self, other):
        return self.bvor(other).bvnot()

    @auto_cast
    def bvxor(self, other):
        return self._solver.BVXor(self.value, other.value)

    @auto_cast
    def bvxnor(self, other):
        return self.bvxor(other).bvnot()

    @auto_cast
    def bvshl(self, other):
        return self._solver.BVShl(self.value, other.value)

    @auto_cast
    def bvlshr(self, other):
        return self._solver.BVLshr(self.value, other.value)

    @auto_cast
    def bvashr(self, other):
        return self._solver.BVAshr(self.value, other.value)

    def bvrol(self, other):
        raise NotImplementedError()

    def bvror(self, other):
        raise NotImplementedError()

    @auto_cast_bool
    def bvcomp(self, other):
        return self.solver.Equal(self.value, other.value)

    bveq = bvcomp

    @auto_cast_bool
    def bvne(self, other):
        return self.bveq(other).bvnot()

    @auto_cast_bool
    def bvult(self, other):
        return self._solver.BVUlt(self.value, other.value)

    @auto_cast_bool
    def bvule(self, other):
        return self._solver.BVUle(self.value, other.value)

    @auto_cast_bool
    def bvugt(self, other):
        return self._solver.BVUgt(self.value, other.value)

    @auto_cast_bool
    def bvuge(self, other):
        return self._solver.BVUge(self.value, other.value)


    @auto_cast_bool
    def bvslt(self, other):
        return self._solver.BVSlt(self.value, other.value)

    @auto_cast_bool
    def bvsle(self, other):
        return self._solver.BVSle(self.value, other.value)

    @auto_cast_bool
    def bvsgt(self, other):
        return self._solver.BVSgt(self.value, other.value)

    @auto_cast_bool
    def bvsge(self, other):
        return self._solver.BVSge(self.value, other.value)

    @auto_cast
    def bvneg(self):
        return self._solver.BVNeg(self.value)

    @auto_cast
    def bvadd(self, other):
        return self._solver.BVAdd(self.value, other.value)

    @auto_cast
    def bvsub(self, other):
        return self._solver.BVSub(self.value, other.value)

    @auto_cast
    def bvmul(self, other):
        return self._solver.BVMul(self.value, other.value)

    @auto_cast
    def bvudiv(self, other):
        return self._solver.BVUdiv(self.value, other.value)

    @auto_cast
    def bvurem(self, other):
        return self._solver.BVUrem(self.value, other.value)

    @auto_cast
    def bvsdiv(self, other):
        # currently not in smt switch 
        raise NotImplementedError()
        return self._solver.BVSdiv(self.value, other.value)

    @auto_cast
    def bvsrem(self, other):
        raise NotImplementedError()
        return self._solver.BVSrem(self.value, other.value)

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


class SMTNumVector(SMTBitVector):
    pass


class UIntVector(SMTNumVector):
    pass

class SMTUIntVector(SMTNumVector):
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

