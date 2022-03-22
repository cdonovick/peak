from peak import Peak, family_closure
import magma as m
from hwtypes import BitVector as BV
import os

def test_custom_verilog():
    vfile = "tests/custom_verilog.v"
    assert os.path.exists(vfile)
    mod = m.define_from_verilog_file(vfile)[0]

    @family_closure
    def Foo_fc(family):

        @family.assemble(locals(), globals())
        class Foo(Peak):
            def __init__(self):
                self.vfoo: mod = mod()
            def __call__(self, I0:BV[16], I1:BV[16]) -> BV[16]:
                tmp = self.vfoo(I0, I1)
                return ~tmp
        return Foo

    Foo_magma = Foo_fc.Magma
    m.compile('tests/build/foo', Foo_magma)