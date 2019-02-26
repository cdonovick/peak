from .. import Peak, Register, Enum
from .lut import Bit

# Field for specifying register modes
#
class Mode(Enum):
    CONST = 0   # Register returns constant in constant field
    VALID = 1   # Register written with clock enable, previous value returned
    BYPASS = 2  # Register is bypassed and input value is returned
    DELAY = 3   # Register written with input value, previous value returned

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
            return self.register(value, True)
        elif mode == Mode.VALID:
            return self.register(value, clk_en)
        else:
            raise NotImplementedError()
