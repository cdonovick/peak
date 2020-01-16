from collections import OrderedDict
from hwtypes import TypeFamily, AbstractBitVector, AbstractBit, BitVector, Bit, is_adt_type
from hwtypes.adt import Product
import functools
from inspect import isclass
from hwtypes import SMTBit
from ast_tools.passes import begin_rewrite, end_rewrite
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
from hwtypes import make_modifier
import warnings


class PeakMeta(type):
    @property
    def input_t(cls):
        if not hasattr(cls.__call__, '_peak_inputs_'):
            raise ValueError("Missing type annotations. Did you forget to decorate __call__ with 'name_outputs'")
        return cls.__call__._peak_inputs_

    @property
    def output_t(cls):
        if not hasattr(cls.__call__, '_peak_outputs_'):
            raise ValueError("Missing type annotations. Did you forget to decorate __call__ with 'name_outputs'")
        return cls.__call__._peak_outputs_

class Peak(metaclass=PeakMeta): pass

def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output type will be stored in fn._peak_outputs__
    The input type will be stored in fn._peak_inputs_
    Will verify that all the inputs have type annotations
    Will also verify that the outputs of running fn will have the correct number of bits
    """
    def decorator(call_fn):
        @functools.wraps(call_fn)
        def call_wrapper(*args, **kwargs):
            results = call_fn(*args, **kwargs)
            single_output = not isinstance(results, tuple)
            if single_output:
                results = (results,)
            for i, (oname, otype) in enumerate(outputs.items()):
                if not isinstance(results[i], otype):
                    raise TypeError(f"result type for {oname} : {type(results[i])} did not match expected type {otype}")
            if single_output:
                results = results[0]
            return results

        #Set all the outputs
        peak_outputs = OrderedDict()
        for oname, otype in outputs.items():
            if not issubclass(otype, (AbstractBitVector, AbstractBit)):
                raise TypeError(f"{oname} is not a Bitvector class")
            peak_outputs[oname] = otype
        call_wrapper._peak_outputs_ = Product.from_fields("Output", peak_outputs)

        #set all the inputs
        arg_offset = 1 if call_fn.__name__ == "__call__" else 0
        peak_inputs = OrderedDict()
        num_inputs = call_fn.__code__.co_argcount
        input_names = call_fn.__code__.co_varnames[arg_offset:num_inputs]
        in_types = call_fn.__annotations__
        in_type_keys = set(in_types.keys())
        # Remove return annotation if it exists
        if "return" in in_type_keys:
            in_type_keys.remove("return")
        if set(input_names) != set(in_type_keys):
            raise TypeError(f"Missing type annotations on inputs: {set(input_names)} != {set(in_type_keys)}")
        for name in input_names:
            input_type= in_types[name]
            peak_inputs[name] = in_types[name]
        call_wrapper._peak_inputs_ = Product.from_fields("Input", peak_inputs)
        return call_wrapper
    return decorator

#This decorator does the following:
#1) Caches the function call
#2) Stores the family closure in Peak._fc_
class family_closure:
    def __init__(self, f):
        self.f = f

        num_inputs = f.__code__.co_argcount
        if num_inputs != 1:
            warnings.warn("Family Closure should take a single input 'family'")
        functools.update_wrapper(self, f)
        self.cache = {}

    def __call__(self, family):
        if family in self.cache:
            return self.cache[family]
        cls = self.f(family)
        if not (isclass(cls) and issubclass(cls, Peak)):
            warnings.warn("Family closure should return a single Peak class")
        else:
            cls._fc_ = self
        self.cache[family] = cls
        return cls

class PeakNotImplementedError(NotImplementedError):
    pass

#This will update the call function of peak appropriately for automapping
#Needs to be called from within the family_closure function
def update_peak(peak_cls, family):
    if family is SMTBit.get_family():
        call = peak_cls.__call__
        for dec in (
            begin_rewrite(),
            ssa(),
            bool_to_bit(),
            if_to_phi(family.Bit.ite),
            end_rewrite()):
            call = dec(call)
        peak_cls.__call__ = call
    return peak_cls


Const = make_modifier("Const")
