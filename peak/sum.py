__all__ =  ['Sum', 'is_sum']

class Sum:
    fields = None

    def __init__(self, a):
        assert type(a) in self.fields
        self.a = a

    def __str__(self):
        return str(self.a)

    def __repr__(self):
        return repr(self.a)

    def __call__(self, *largs, **kwargs):
        return self(*largs, **kwargs)

    def match(self):
        return type(self.a), self.a

def is_sum(sum):
    return isinstance(sum, Sum)


