from collections.abc import MutableMapping
from collections import deque

class SubTypeDict(MutableMapping):
    def __init__(self, d=()):
        self._d = dict(d)

    def __getitem__(self, key: type):
        for T in key.mro():
            try:
                return self._d[T]
            except KeyError:
                pass
        raise KeyError()

    def __setitem__(self, key, value):
        if not isinstance(key, type):
            raise TypeError('Keys must be types')
        self._d[key] = value

    def __delitem__(self, key):
        del self._d[key]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)
