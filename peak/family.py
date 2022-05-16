from abc import ABCMeta, abstractmethod
import functools as ft
import logging

from ast_tools.passes import apply_passes
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
from ast_tools import SymbolTable
import hwtypes
from hwtypes.modifiers import strip_modifiers
from hwtypes import Product
import magma as m

from .assembler import Assembler
from .assembler import AssembledADT, MagmaADT
from .black_box import BlackBox

logger = logging.getLogger(__name__)

__ALL__ = ['PyFamily', 'SMTFamily', 'MagmaFamily']

def _compose(f, g):
    def wrapped(*args, **kwargs):
        return f(g(*args, **kwargs))
    return wrapped


class AbstractFamily(metaclass=ABCMeta):
    # init accepts **kwargs to allow specific families to specify options
    # particular to them without needing to thread them through all families.
    def __init__(self, **kwargs):
        if kwargs:
            msg = [f"Unused init kwargs for familiy of {type(self)}"]
            for k, v in kwargs.items():
                msg.append(f"\t{k} = {v} :: {type(v)}")
            logger.debug('\n'.join(msg))

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

    # assemble accepts kwargs for similar reasons to init
    @abstractmethod
    def assemble(self, locals, globals, **kwargs):
        if kwargs:
            msg = [f"Unused assemble kwargs for familiy of {type(self)}"]
            for k, v in kwargs.items():
                msg.append(f"\t{k} = {v} :: {type(v)}")
            logger.debug('\n'.join(msg))
        def deco(cls): return cls
        return deco

    # an alias for assemble
    def compile(self, locals, globals, **kwargs):
        return self.assemble(locals, globals, **kwargs)

    @abstractmethod
    def get_adt_t(self, adt_t): pass

    @abstractmethod
    def get_constructor(self, adt_t): pass

    @abstractmethod
    def gen_register(self, T, init): pass


class _AsmFamily(AbstractFamily):
    '''
    Defines get_adt_t as the assembled version
    '''
    def  __init__(self, assembler, aadt_t, asm_extras=(), **kwargs):
        super().__init__(**kwargs)
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
    def __init__(self, passes=(), **kwargs):
        super().__init__(**kwargs)
        self._passes = passes

    def assemble(self, locals, globals, **kwargs):
        env = SymbolTable(locals, globals)
        s_deco = super().assemble(locals, globals, **kwargs)
        def deco(cls):
            # only rewrite if necesarry
            if not self._passes:
                return cls
            cls.__call__ = apply_passes(self._passes, env=env)(cls.__call__)
            return cls
        return _compose(deco, s_deco)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._passes == other._passes
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._passes)

    __ne__ = AbstractFamily.__ne__


_REG_CACHE = {}
_ATTR_REG_CACHE = {}
class _RegFamily(AbstractFamily):
    def gen_register(self, T, init):
        key = (type(self), T, init)
        try:
            return _REG_CACHE[key]
        except KeyError:
            pass

        family = self

        # avoids circular import
        from peak import Peak

        @family.assemble(locals(), globals())
        class Register(Peak):
            def __init__(self):
                self.value: T = T(init)

            def __call__(self, value: T, en: family.Bit) -> T:
                assert value is not None
                retvalue = self.value
                if en:
                    self.value = value
                return retvalue

            def prev(self) -> T:
                # This is not quite right and doesn't match
                # magma semantics completely. May only be used
                # as a peak method prior to __call__
                return self.value

        return _REG_CACHE.setdefault(key, Register)

    def gen_attr_register(self, T, init):
        key = (type(self), T, init)
        try:
            return _ATTR_REG_CACHE[key]
        except KeyError:
            pass
        family = self

        # avoids circular import
        from peak import Peak

        class Register(Peak):
            def __init__(self):
                self.value: T = T(init)

            def _poke_(self, value):
                self.value = value

            def _peak_(self):
                return self.value

        return _ATTR_REG_CACHE.setdefault(key, Register)


class _BBFamily(AbstractFamily):
    def assemble(self, locals, globals, **kwargs):
        s_deco = super().assemble(locals, globals, **kwargs)
        def deco(cls):
            if issubclass(cls, BlackBox):
                cls.create_call()
            return cls
        return _compose(deco, s_deco)


class PyFamily(_RegFamily):
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

    def get_adt_t(self, adt_t):
        return adt_t

    def get_constructor(self, adt_t):
        return adt_t

    def assemble(self, locals, globals, **kwargs):
        return super().assemble(locals, globals, **kwargs)



# Strategically put _AsmFamily first so eq dispatches to it
class _StdMix(_AsmFamily, _RewriterFamily):
    '''
    Mixin which defines an init and assemble with the usual arguments
    Rewrites __call__ to ssa
    Also assembles adts
    '''
    def __init__(self, assembler=None, **kwargs):
        if assembler is None:
            assembler=Assembler

        assert "assembler" not in kwargs

        passes = (ssa(), bool_to_bit(), if_to_phi(self.Bit.ite))
        super().__init__(assembler, AssembledADT, passes=passes, **kwargs)

    def assemble(self, locals, globals, **kwargs):
        s_deco = super().assemble(locals, globals, **kwargs)
        def deco(cls):
            input_t = cls.__call__._input_t
            output_t = cls.__call__._output_t

            cls = s_deco(cls)

            cls.__call__._input_t = input_t
            cls.__call__._output_t = output_t
            return cls

        return deco

class PyXFamily(_StdMix, PyFamily): pass


# Put _BBFamily first so it switchs out the __call__ after its been ssa'd
class SMTFamily(_BBFamily, _StdMix, _RegFamily):
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

    def assemble(self, locals, globals, **kwargs):
        s_deco = super().assemble(locals, globals, **kwargs)
        def deco(cls):
            input_t = cls.__call__._input_t
            output_t = cls.__call__._output_t

            cls = s_deco(cls)

            cls.__call__._input_t = input_t
            cls.__call__._output_t = output_t
            return cls

        return deco


class MagmaFamily(_AsmFamily):
    '''
    Family for magma
    Assembles adts and runs sequential
    '''

    def __init__(self, assembler=None, **kwargs):
        if assembler is None:
            assembler=Assembler
        super().__init__(assembler, MagmaADT, (m.Direction.Undirected,), **kwargs)

    @property
    def Bit(self):
        return m.Bit

    @property
    def BitVector(self):
        return m.Bits

    @property
    def Signed(self):
        return m.SInt

    @property
    def Unsigned(self):
        return m.UInt

    def gen_register(self, T, init):
        return m.Register(T, init,
            has_enable=True,
            reset_type=m.AsyncReset,
            name_map=m.generator.ParamDict(CE='en', I='value'),
        )

    def gen_attr_register(self, T, init):
        return m.Register(T, init,
            has_enable=False,
            reset_type=m.AsyncReset,
        )


    def assemble(self, locals, globals, set_port_names: bool = False, **kwargs):
        def magmafy(t_):
            if isinstance(t_, tuple):
                return tuple(magmafy(t__) for t__ in t_)
            t_ = strip_modifiers(t_)
            if hwtypes.is_adt_type(t_):
                return self.get_adt_t(t_)
            elif issubclass(t_, hwtypes.AbstractBitVector):
                t_fam  = t_.get_family()
                size = t_.size
                # There should really be a better way to check this
                if issubclass(t_, t_fam.Signed):
                    return self.Signed[size]
                elif issubclass(t_, t_fam.Unsigned):
                    return self.Unsigned[size]
                else:
                    return self.BitVector[size]
            elif issubclass(t_, hwtypes.AbstractBit):
                return self.Bit
            else:
                return t_

        env = SymbolTable(locals, globals)

        s_deco = super().assemble(locals, globals, **kwargs)

        def deco(cls):
            call = cls.__call__
            output_t = getattr(call, '_output_t', None)
            kwargs = {}
            if output_t is not None and issubclass(output_t, Product) and set_port_names:
                kwargs['output_port_names'] = tuple(output_t.field_dict.keys())

            annotations = {}
            for arg, t_ in call.__annotations__.items():
                annotations[arg] = magmafy(t_)
            cls = m.sequential2(env=env,
                    annotations=annotations,
                    reset_type=m.AsyncReset,
                    **kwargs,
                    )(cls)
            return cls
        return _compose(deco, s_deco)
