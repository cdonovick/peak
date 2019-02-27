from collections import OrderedDict
from bit_vector import BitVector
import functools

class Peak:
    pass


def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output types will be stored in fn.___peak_outputs___
    The input types will be stored in fn.___peak_inputs___
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
            for i, (oname,otype) in enumerate(outputs.items()):
                if results[i].num_bits != otype(0).num_bits:
                    raise TypeError(f"{results[i].num_bits} != {otype(0).num_bits}")
            if single_output:
                results = results[0]
            return results

        #Set all the outputs
        call_wrapper._peak_outputs_ = OrderedDict()
        for oname,otype in outputs.items():
            if not issubclass(otype,BitVector):
                raise TypeError(f"{oname} is not a Bitvector class")
            call_wrapper._peak_outputs_[oname] = otype

        #set all the inputs
        call_wrapper._peak_inputs_ = OrderedDict()
        num_inputs = call_fn.__code__.co_argcount
        input_names = call_fn.__code__.co_varnames[1:num_inputs]
        in_types = call_fn.__annotations__
        if set(input_names) != set(in_types.keys()):
            raise TypeError("Missing type annotations on inputs")
        for name in input_names:
            call_wrapper._peak_inputs_[name] = in_types[name]

        return call_wrapper
    return decorator


