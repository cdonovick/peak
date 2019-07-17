def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False

