from peak import Peak, Enum, Bits, Struct, Union, match

DATAWIDTH = 16

Bit = Bits(1)
Data = Bits(DATAWIDTH)

class RegMode(Enum):
    CONST = 0
    VALID = 1
    BYPASS = 2
    DELAY = 3

class Register(Peak):
    def __init__(self, init:Data):
        self.init = init
        self.reset()

    def reset(self):
        self.value = self.init

    def __call__(self, value:Data, clk_en:Bit) -> Data:
        retvalue = self.value
        if clk_en:
            self.value = value
        return retvalue

class RegisterMode(Peak):
    def __init__(self, init:Data):
        self.register = Register(init)

    def reset(self):
        self.register.reset()

    def __call__(self, value, mode):
        if mode in [DELAY, VALID, CONST]:
            return self.register(value, mode == DELAY or clk_en)
        elif mode == BYPASS:
            return value
        else:
            raise NotImplementedError()


class ALU(Peak):
    #def __init__(self, ops, opcode, width, signed=False, double=False):
    def __init__(self, ops):
        self.ops = ops
        self._carry = False

    def __call__(self, op:Op, signed:Bit, a:Data, b:Data, c:Data, d:Data):
        return self.ops[op](a, b, c, d)


class COND(Peak):
    def __init__(self):
        pass

    def __call__(self, a, b, res, signed, cond):
        return_vals = self.compare(a, b, res)
        return self.cond(*return_vals)

    def compare(self, a, b, res, signed):
        eq = a == b
        eq = eq.as_int()
        a_msb = msb(a)
        b_msb = msb(b)
        c_msb = msb(res)
        if signed:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (~a_msb & b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (a_msb & ~b_msb) | eq) & 1
        else:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (a_msb & ~b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (~a_msb & b_msb) | eq) & 1
        return Bit(ge), Bit(eq), Bit(le)


class PE(Peak):

    def __init__(self, inst: Inst):
        self.inst = inst
        # initialize state

    def __call__(self, data0:, data1:, bit0:, bit1:, bit2:) -> res:, res_p: :
        # match instruction
        pass
