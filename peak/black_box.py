from functools import lru_cache

@lru_cache(None)
def get_black_boxes(obj, path=()):
    """Gets references to all the black boxes in the hierarchical circuit"""

    # Hack to avoid circular import
    from .peak import Peak

    if not isinstance(obj, Peak):
        raise ValueError(f"{obj} needs to be a Peak object")
    if isinstance(obj, BlackBox):
        return {path: obj}
    ret = {}
    for field, obj in obj.__dict__.items():
        if isinstance(obj, Peak):
            ret = {**ret, **get_black_boxes(obj, path + (field,))}
    return ret

@lru_cache(None)
def get_black_box(obj, path):
    """Gets a specific black box given a path"""
    # Hack to avoid circular import
    from .peak import Peak

    for field in path:
        obj = getattr(obj, field, None)
        if obj is None:
            raise ValueError(f"{obj} does not have attribute {field}")
        if not isinstance(obj, Peak):
            raise ValueError(f"{obj} must be a peak class")
    return obj


class BlackBox:

    def __init__(self):
        self._input_vals = None
        self._output_vals = None

    @classmethod
    def create_call(cls):
        old_call = cls.__call__
        def __call__(self, *args, **kwargs):
            input_t = type(self).input_t
            if self._output_vals is None:
                raise ValueError(f"{self}: Need to call _set_outputs before __call__")
            if (len(args) > 0) == (len(kwargs) > 0):
                raise ValueError(f"{self}: Can only call with either *args or **kwargs")
            if len(args) > 0:
                if len(args) != len(input_t.field_dict):
                    raise ValueError(f"{self} need to call with input_t {list(input_t.field_dict.items())}")
                self._input_vals = tuple(args)
            else:
                if kwargs.keys() != input_t.field_dict.keys():
                    raise ValueError(f"{self} need to call with input_t {list(input_t.field_dict.items())}")
                self._input_vals = tuple(kwargs.values())
            return self._output_vals
        if hasattr(old_call, "_input_t"):
            assert hasattr(old_call, "_output_t")
            __call__._input_t = old_call._input_t
            __call__._output_t = old_call._output_t
        cls.__call__ = __call__

    def _get_inputs(self):
        if self._input_vals is None:
            raise ValueError(f"{self}: Need to call __call__ before _get_inputs")
        return self._input_vals

    def _set_outputs(self, *args):
        output_t = type(self).output_t
        if len(args) != len(output_t.field_dict):
            raise ValueError(f"{self} need to set outputs with output_t {list(output_t.field_dict.items())}")
        if len(args)==1:
            self._output_vals = args[0]
        else:
            self._output_vals = args

