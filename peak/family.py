from abc import ABCMeta, abstractmethod
import functools as ft

from ast_tools.passes import begin_rewrite, end_rewrite
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
import hwtypes
import magma as m

from .assembler import Assembler
from .assembler import AssembledADT, MagmaADT

__ALL__ = ['PyFamily', 'SMTFamily', 'MagmaFamily']

class AbstractFamily(metaclass=ABCMeta):
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


class _AsmFamily(AbstractFamily):
    '''
    Family that swaps out annotations on __call__ with assembled variants
    Also defines get_adt_t as the assembled version
    '''
    def  __init__(self, assembler, aadt_t, *asm_extras):
        self._assembler = assembler
        self._asm_extras = asm_extras
        self._aadt_t = aadt_t

    def assemble(self, locals, globals):
        def deco(cls):
            call = cls.__call__
            annotations = {}
            for arg, t in call.__annotations__.items():
                if hwtypes.is_adt_type(t):
                    t = self.get_adt_t(t)
                annotations[arg] = t
            call.__annotations__ = annotations
            return cls
        return deco

    def get_adt_t(self, adt_t):
        if not hwtypes.is_adt_type(t):
            raise TypeError(f'expected adt_t not {adt_t}')

        return self._aadt_t[(adt_t, self._assembler, self.BitVector, *self._asm_extras)]

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
            return cls
        return deco

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
        _asm_deco = _AsmFamily.assemble(self, locals, globals)
        _rew_deco = _RewriterFamily.assemble(self, locals, globals)
        def deco(cls):
            input_t = cls.__call__._input_t
            output_t = cls.__call__._output_t
            cls = _asm_deco(_rew_deco(cls))
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
        env = SymbolTable(locals, globals)
        _asm_deco = super().assemble(locals, globals)
        def deco(cls):
            cls = _asm_deco(cls)
            cls = magma.circuit.sequential(cls, env=env)
            return cls
        return deco
