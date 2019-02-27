from collections import OrderedDict
from bit_vector import BitVector

class Peak:
    pass


def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output types will be stored in fn.__peak_outputs__
    The input types will be stored in fn.__peak_inputs__
    Will verify that all the inputs have type annotations
    Will also verify that the outputs of running fn will have the correct number of bits
    """
    def decorator(call_fn):
        def call_wrapper(*args,**kwargs):
            results = call_fn(*args,**kwargs)
            if not isinstance(results,tuple):
                results = (results,)
            for i, (oname,otype) in enumerate(outputs.items()):
                assert results[i].num_bits == otype(0).num_bits, f"{results[i].num_bits} != {otype(0).num_bits}"
            return results

        #Set all the outputs
        call_wrapper.__peak_outputs__ = OrderedDict()
        for oname,otype in outputs.items():
            assert issubclass(otype,BitVector), f"{oname} is not a Bitvector class"
            call_wrapper.__peak_outputs__[oname] = otype

        #set all the inputs
        call_wrapper.__peak_inputs__ = OrderedDict()
        num_inputs = call_fn.__code__.co_argcount
        input_names = call_fn.__code__.co_varnames[1:num_inputs]
        in_types = call_fn.__annotations__
        assert set(input_names) == set(in_types.keys()), "Missing type annotations on inputs"
        for name in input_names:
            call_wrapper.__peak_inputs__[name] = in_types[name]

        return call_wrapper
    return decorator


