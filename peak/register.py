from .peak import Peak

class Register(Peak):
    def __init__(self, init):
        self.init = init
        self.reset()

    def reset(self):
        self.value = self.init

    def __call__(self, value=None, en=1):
        retvalue = self.value
        if value is not None and en:
            assert value is not None
            self.value = value
        return retvalue

