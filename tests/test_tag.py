import pytest
from hwtypes.adt import Sum

from peak.bitfield import tag

def test_tag():
    @tag({int : 0, str : 1})
    class S(Sum[int ,str]): pass

    assert S.tags[int] == 0
    assert S.tags[str] == 1

    with pytest.raises(TypeError):
        @tag()
        class S: pass

    with pytest.raises(ValueError):
        @tag({int : 0, str : 1, object : 2})
        class S(Sum[int ,str]): pass

    with pytest.raises(ValueError):
        @tag({int : 0})
        class S(Sum[int ,str]): pass

    with pytest.raises(TypeError):
        @tag({int : 'a', str : 1})
        class S(Sum[int ,str]): pass




