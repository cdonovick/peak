from ..riscv import family
from ast_tools.passes import loop_unroll


PyFamily = family.PyFamily

class SMTFamily(family.SMTFamily):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._passes = loop_unroll(), *self._passes
