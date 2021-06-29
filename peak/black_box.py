
class BlackBox:

    @staticmethod
    def get_black_boxes(pe, path=()):

        #Hack to avoid circular import
        from .peak import Peak

        assert isinstance(pe, Peak)
        ret = {}
        for field, obj in pe.__dict__.items():
            if isinstance(obj, BlackBox):
                ret[path + (field,)] = obj
            if isinstance(obj, Peak):
                ret = {**ret, **BlackBox.get_black_boxes(obj, path + (field,))}
        return ret

    @staticmethod
    def get(obj, path):
        # Hack to avoid circular import
        from .peak import Peak

        for field in path:
            obj = getattr(obj, field, None)
            if obj is None:
                raise ValueError(f"{obj} does not have attribute {field}")
            if not isinstance(obj, Peak):
                raise ValueError(f"{obj} must be a peak class")
        return obj


    def __init__(self):
        self._input_vals = None
        self._output_vals = None

    def __call__(self, *args):
        if self._output_vals is None:
            raise ValueError(f"{self}: Need to call _set_outputs before __call__")
        self._input_vals = args
        ret = self._output_vals
        self._output_vals = None
        return ret

    def _get_inputs(self):
        if self._input_vals is None:
            raise ValueError(f"{self}: Need to call __call__ before _get_inputs")
        ret = self._input_vals
        self._input_vals = None
        return ret

    def _set_outputs(self, *args):
        if len(args)==1:
            self._output_vals = args[0]
        else:
            self._output_vals = args

