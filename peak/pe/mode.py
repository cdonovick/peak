from .. import Peak, Register
from .lut import Bit

class Mode:
    CONST = 0
    VALID = 1
    BYPASS = 2
    DELAY = 3

class RegisterMode(Peak):
    def __init__(self, init = 0):
        self.register = Register(init)

    def reset(self):
        self.register.reset()

    def __call__(self, mode:Mode, const, value, clk_en:Bit):
        if   mode == Mode.CONST:
            return const
        elif mode == Mode.BYPASS:
            return value
        elif mode == Mode.DELAY:
            return self.register(value, mode == Mode.DELAY)
        elif mode == Mode.VALID:
            return self.register(value, clk_en)
        else:
            raise NotImplementedError()
