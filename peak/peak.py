from collections import OrderedDict
from hwtypes import TypeFamily, AbstractBitVector, AbstractBit, BitVector, Bit, is_adt_type
import functools

class Peak:
    @classmethod
    def get_inputs(cls):
        assert hasattr(cls.__call__, '_peak_inputs_')
        return cls.__call__._peak_inputs_

    @classmethod
    def get_outputs(cls):
        assert hasattr(cls.__call__, '_peak_inputs_')
        return cls.__call__._peak_inputs_


def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output types will be stored in fn._peak_outputs__
    The input types will be stored in fn._peak_inputs_
    The ISA will be stored in fn._peak_isa_
    Will verify that all the inputs have type annotations
    Will also verify that the outputs of running fn will have the correct number of bits
    """
    def decorator(call_fn):
        @functools.wraps(call_fn)
        def call_wrapper(*args,**kwargs):
            results = call_fn(*args,**kwargs)
            single_output = not isinstance(results,tuple)
            if single_output:
                results = (results,)
            for i, (oname, otype) in enumerate(outputs.items()):
                if not isinstance(results[i], otype):
                    raise TypeError(f"result type for {oname} : {type(results[i])} did not match expected type {otype}")
            if single_output:
                results = results[0]
            return results

        #Set all the outputs
        call_wrapper._peak_outputs_ = OrderedDict()
        for oname,otype in outputs.items():
            if not issubclass(otype, (AbstractBitVector, AbstractBit)):
                raise TypeError(f"{oname} is not a Bitvector class")
            call_wrapper._peak_outputs_[oname] = otype

        #set all the inputs
        arg_offset = 1 if call_fn.__name__ == "__call__" else 0
        call_wrapper._peak_inputs_ = OrderedDict()
        num_inputs = call_fn.__code__.co_argcount
        input_names = call_fn.__code__.co_varnames[arg_offset:num_inputs]
        in_types = call_fn.__annotations__
        in_type_keys = set(in_types.keys())
        # Remove return annotation if it exists
        if "return" in in_type_keys:
            in_type_keys.remove("return")
        if set(input_names) != set(in_type_keys):
            raise TypeError(f"Missing type annotations on inputs: {set(input_names)} != {set(in_type_keys)}")
        isa = []
        for name in input_names:
            input_type= in_types[name]
            if is_adt_type(input_type):
                isa.append((name,input_type))
                continue
            call_wrapper._peak_inputs_[name] = in_types[name]
        if len(isa) == 0:
            raise TypeError("Need to pass peak ISA instruction to __call__")
        if len(isa) > 1:
            raise NotImplementedError("Can only pass in single instruction")
        call_wrapper._peak_isa_ = isa[0]
        return call_wrapper
    return decorator

class PeakNotImplementedError(NotImplementedError):
    pass


