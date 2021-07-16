from hwtypes import make_modifier, AbstractBitVector, AbstractBit
from .features import gen_input_t as _gen_input_t
from .features import gen_output_t as _gen_output_t
from .features import typecheck as _typecheck
from .ports import Port, Direction

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
            gen_ports=False,
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

            if not gen_ports:
                cls._ports_ = {}
                return cls

            if cls.input_t.field_dict.keys() & cls.output_t.field_dict.keys():
                raise TypeError('Cannot have input with same name as output')

            inputs = cls.input_t.field_dict
            outputs = cls.output_t.field_dict
            cls._ports_ = {
                k: Port[v](Direction.IN, cls, k)
                for k, v in inputs.items()
            }
            cls._ports_.update({
                k: Port[v](Direction.OUT, cls, k)
                for k, v in outputs.items()
            })
        else:
            cls._ports_ = {}


        return cls

    def __call__(cls, *args, **kwargs):
        inst = super().__call__(*args, **kwargs)
        inst._instances_ = instances = []
        for v in inst.__dict__.values():
            if isinstance(v, Peak):
                instances.append(v)

        # this is hacky there should probably be a better
        # way to bind the instances ports
        inst._ports_ = ports = {}
        inst._inputs_ = inputs = {}
        inst._outputs_ = outputs = {}

        for k, p in cls._ports_.items():
            ports[k] = p._clone(inst)
            if p.direction is Direction.IN:
                inputs[k] = None
            else:
                # This isn't going to work for adt outputs...
                outputs[k] = type(p).bound_t()
        inst._init_done_ = True
        return inst


class Peak(metaclass=PeakMeta):
    def __getattr__(self, attr):
        try:
            port = self._ports_[attr]
        except KeyError:
            raise AttributeError(attr) from None

        if port.direction is Direction.IN:
            # return a port object for inputs
            return port
        else:
            # return the value of the output for output ports
            # this allows x.in @= y.out + 1
            return self._outputs_[attr]


    def __setattr__(self, attr, value):
        try:
            init_done = super().__getattribute__('_init_done_')
        except AttributeError:
            init_done = False

        if not init_done:
            return super().__setattr__(attr, value)

        port = self._ports_.get(attr, None)

        if port is None:
            return super().__setattr__(attr, value)

        assert isinstance(port, Port)

        if port is not value:
            raise AttributeError(f'cannot overwrite port {attr}')

        if port.direction is not Direction.IN:
            raise AttributeError(f'cannot write to output port {attr}')
        # don't need to do anything because port is value


    def _eval_(self):
        last_state = None
        next_state = self._eval_state_
        # this isn't going to work for smt
        while last_state != next_state:
            outputs = self(**self._inputs_)
            # outputs might be tuple or it be a single value
            if len(self._outputs_) == 1 and not isinstance(outputs, tuple):
                self._outputs_ = {k: outputs for i, k in enumerate(self._outputs_)}
            else:
                assert isinstance(outputs, tuple)
                self._outputs_ = {k: outputs[i] for i, k in enumerate(self._outputs_)}

            for i in self._instances_:
                i._eval_()

            last_state = next_state
            next_state = self._eval_state_

    def _update_state_(self):
        for i in self._instances_:
            i._update_state_()

    def _step_(self):
        self._eval_()
        self._update_state_()

    @property
    def _eval_state_(self):
        return self._inputs_, self._outputs_, tuple(i._eval_state_ for i in self._instances_)


class PeakNotImplementedError(NotImplementedError):
    pass

Const = make_modifier("Const")
