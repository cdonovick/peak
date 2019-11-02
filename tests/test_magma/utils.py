import magma as m
import functools

def reset_magma(fn):
    @functools.wraps(fn)
    def dec(*args,**kwargs):
        fn(*args,**kwargs)
        m.backend.coreir_.CoreIRContextSingleton().reset_instance()
        m.clear_cachedFunctions()
    return dec

