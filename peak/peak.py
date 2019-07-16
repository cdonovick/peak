from collections import OrderedDict
from hwtypes import TypeFamily, AbstractBitVector, AbstractBit, is_adt_type
from hwtypes.adt import Product, Sum, Enum, Tuple
import functools
import inspect
import textwrap


def _rebind_type(T,family):
    if T in (AbstractBitVector,AbstractBit,Product,Sum,Tuple, Enum):
        return T
    if not inspect.isclass(T):
        return T
    if issubclass(T,AbstractBitVector):
        if T.size is None: #This is BitVector
            return family.BitVector
        else:
            return family.BitVector[T.size]
    elif issubclass(T,AbstractBit):
        return family.Bit
    elif issubclass(T,Product):
        return Product.from_fields(T.__name__,{field:_rebind_type(t,family) for field,t in T.field_dict.items()})
    elif issubclass(T,Enum):
        return T
    elif issubclass(T,Sum):
        raise NotImplementedError("NYI dynamic Sum constructor")
        #return Sum.from_fields(T.__name__,{field:_rebind_type(t,family) for field,t in T.field_dict.items()})
    else:
        return T


#This will save the locals and globals in Class._env_
class PeakMeta(type):
    def __new__(mcs,name,bases,attrs,**kwargs):
        stack = inspect.stack()
        env = {}
        for i in reversed(range(1,len(stack))):
            for key, value in stack[i].frame.f_globals.items():
                env[key] = value
        for i in reversed(range(1,len(stack))):
            for key, value in stack[i].frame.f_locals.items():
                env[key] = value
        cls = super().__new__(mcs,name,bases,attrs,**kwargs)
        cls._env_ = env
        return cls

    #This will rebind the class to a specific family
    def rebind(cls,family):
        assert hasattr(cls,"_env_")
        env = {k:_rebind_type(t,family) for k,t in cls._env_.items()}
        indented_program_txt = inspect.getsource(cls)
        program_txt = textwrap.dedent(indented_program_txt)
        exec_ls = {}
        exec(program_txt,env,exec_ls)
        return exec_ls[cls.__name__]

class Peak(metaclass=PeakMeta):
    pass


def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output types will be stored in fn._peak_outputs__
    The input types will be stored in fn._peak_inputs_
    Will verify that all the inputs have type annotations
    Will also verify that the outputs of running fn will have the correct type 
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
        for name in input_names:
            input_type= in_types[name]
            call_wrapper._peak_inputs_[name] = in_types[name]

        return call_wrapper
    return decorator

class PeakNotImplementedError(NotImplementedError):
    pass

class PeakUnreachableError(NotImplementedError):
    pass


