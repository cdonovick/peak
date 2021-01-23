import pytest
import magma


@pytest.fixture(autouse=True)
def magma_test():
    magma.clear_cachedFunctions()
    magma.frontend.coreir_.ResetCoreIR()
    magma.generator.reset_generator_cache()
