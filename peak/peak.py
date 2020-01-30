from hwtypes import make_modifier
from .features import gen_input_t as _gen_input_t
from .features import gen_output_t as _gen_output_t
from .features import typecheck as _typecheck

class PeakMeta(type):
    @property
    def input_t(cls):
        return cls.__call__._input_t

    @property
    def output_t(cls):
        return cls.__call__._output_t

    def __new__(mcs, name, bases, attrs,
            gen_input_t=True,
            gen_output_t=True,
            typecheck=False,
            **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        if "__call__" in attrs:
            if gen_output_t:
                cls.__call__ = _gen_output_t(cls.__call__)
            if gen_input_t:
                cls.__call__ = _gen_input_t(cls.__call__)
            if typecheck:
                cls.__call__ = _typecheck(cls.__call__)

        return cls

class Peak(metaclass=PeakMeta): pass

class PeakNotImplementedError(NotImplementedError):
    pass

Const = make_modifier("Const")
