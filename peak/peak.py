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


def _is_dunder(name: str) -> bool:
    return (len(name) > 4
            and name[:2] == name[-2:] == '__'
            and name[2] != '_' and name[-3] != '_')

# a sentinel
_null = object()

class Peak(metaclass=PeakMeta):
    # enable a descriptor like protocol on instance attributes
    def __getattribute__(self, attr):
        val = super().__getattribute__(attr)

        if _is_dunder(attr):
            return val

        try:
            getter = val._peak_
        except AttributeError:
            return val

        return getter()

    def __setattr__(self, attr, value):
        if _is_dunder(attr):
            return super().__setattr__(attr, value)

        try:
            current = super().__getattribute__(attr)
        except AttributeError:
            return super().__setattr__(attr, value)

        setter = getattr(current, '_poke_', _null)

        if setter is _null:
            return super().__setattr__(attr, value)
        else:
            return setter(value)


class PeakNotImplementedError(NotImplementedError):
    pass

Const = make_modifier("Const")
