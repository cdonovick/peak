from abc import ABCMeta, abstractmethod
import functools as ft

from ast_tools.passes import begin_rewrite, end_rewrite
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
from ast_tools import SymbolTable
import hwtypes
from hwtypes.modifiers import strip_modifiers
import magma as m

from .assembler import Assembler
from .assembler import AssembledADT, MagmaADT

__ALL__ = ['PyFamily', 'SMTFamily', 'MagmaFamily']

class AbstractFamily(metaclass=ABCMeta):
    def __eq__(self, other):
        if isinstance(other, type(self)):
            return True
        else:
            return NotImplemented

    def __ne__(self, other):
        eq = (self == other)
        if eq is NotImplemented:
            return NotImplemented
        else:
            return not eq

    def __hash__(self):
        return 0

    @property
    @abstractmethod
    def Bit(self): pass

    @property
    @abstractmethod
    def BitVector(self): pass

    @property
    @abstractmethod
    def Unsigned(self): pass

    @property
    @abstractmethod
    def Signed(self): pass

    @abstractmethod
    def assemble(self, locals, globals): pass

    @abstractmethod
    def get_adt_t(self, adt_t): pass

    @abstractmethod
    def get_constructor(self, adt_t): pass

class _AsmFamily(AbstractFamily):
    '''
    Defines get_adt_t as the assembled version
    '''
    def  __init__(self, assembler, aadt_t, *asm_extras):
        self._assembler = assembler
        self._aadt_t = aadt_t
        self._asm_extras = asm_extras

    def get_adt_t(self, adt_t):
        if issubclass(adt_t, (self.Bit, self.BitVector)):
            return adt_t
        if not hwtypes.is_adt_type(adt_t):
            raise TypeError(f'expected adt_t not {adt_t}')

        return self._aadt_t[(adt_t, self._assembler, self.BitVector, *self._asm_extras)]

    def get_constructor(self, adt_t):
        return self.get_adt_t(adt_t).from_fields

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (self._assembler == other._assembler
                    and self._aadt_t == other._aadt_t
                    and self._asm_extras == other._asm_extras)
        else:
            return NotImplemented

    def __hash__(self):
        return 2*hash(self._assembler) + 3*hash(self._aadt_t) + 5*hash(self._asm_extras)

    __ne__ = AbstractFamily.__ne__

class _RewriterFamily(AbstractFamily):
    '''
    Family that applies ast_tools passes to __call__
    '''
    def __init__(self, passes=()):
        self._passes = passes

    def assemble(self, locals, globals):
        env = SymbolTable(locals, globals)
        def deco(cls):
            if not self._passes:
                return cls
            # only rewrite if necesarry
            call = cls.__call__
            call = begin_rewrite(env=env)(call)
            for dec in self._passes:
                call = dec(call)
            call = end_rewrite()(call)
            cls.__call__ = call
            return cls
        return deco

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._passes == other._passes
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._passes)

    __ne__ = AbstractFamily.__ne__

class PyFamily(AbstractFamily):
    '''
    Pure python family
    Doesn't perform any transformation or do anything special
    '''
    @property
    def Bit(self):
        return hwtypes.Bit

    @property
    def BitVector(self):
        return hwtypes.BitVector

    @property
    def Signed(self):
        return hwtypes.SIntVector

    @property
    def Unsigned(self):
        return hwtypes.UIntVector

    def assemble(self, locals, globals):
        def deco(cls):
            return cls
        return deco

    def get_adt_t(self, adt_t):
        return adt_t

    def get_constructor(self, adt_t):
        return adt_t

# Strategically put _AsmFamily first so eq dispatches to it
class SMTFamily(_AsmFamily, _RewriterFamily):
    '''
    Rewrites __call__ to ssa
    Also assembles adts
    '''
    def __init__(self, assembler=None):
        if assembler is None:
            assembler=Assembler

        _AsmFamily.__init__(self, assembler, AssembledADT)
        _RewriterFamily.__init__(self, (ssa(), bool_to_bit(), if_to_phi(self.Bit.ite)))

    @property
    def Bit(self):
        return hwtypes.SMTBit

    @property
    def BitVector(self):
        return hwtypes.SMTBitVector

    @property
    def Signed(self):
        return hwtypes.SMTSIntVector

    @property
    def Unsigned(self):
        return hwtypes.SMTUIntVector

    def assemble(self, locals, globals):
        _rew_deco = _RewriterFamily.assemble(self, locals, globals)
        def deco(cls):
            input_t = cls.__call__._input_t
            output_t = cls.__call__._output_t
            cls = _rew_deco(cls)
            cls.__call__._input_t = input_t
            cls.__call__._output_t = output_t
            return cls
        return deco

class MagmaFamily(_AsmFamily):
    '''
    Family for magma
    Assembles adts and runs sequential
    '''

    def __init__(self, assembler=None):
        if assembler is None:
            assembler=Assembler
        super().__init__(assembler, MagmaADT, m.Direction.Undirected)

    @property
    def Bit(self):
        return m.Bit

    @property
    def BitVector(self):
        # Because this is how every other impl of BitVector works
        return m.UInt

    @property
    def Signed(self):
        return m.SInt

    @property
    def Unsigned(self):
        return m.UInt

    def assemble(self, locals, globals):
        def adtify(t_):
            if isinstance(t_, tuple):
                return tuple(adtify(t__) for t__ in t_)
            t_ = strip_modifiers(t_)
            if hwtypes.is_adt_type(t_):
                return self.get_adt_t(t_)
            else:
                return t_
        env = SymbolTable(locals, globals)
        def deco(cls):
            call = cls.__call__
            annotations = {}
            for arg, t_ in call.__annotations__.items():
                annotations[arg] = adtify(t_)
            cls = m.sequential2(env=env, annotations=annotations)(cls)
            return cls
        return deco
