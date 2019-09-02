from contextlib import contextmanager


@contextmanager
def as_class(obj, new_class):
    """
    Temporarily replace the `obj` class with `new_class`.
    A typical use is to convert user instance to the ProxyUser custom class to use its extended functionality
    """
    old_class = obj.__class__
    obj.__class__ = new_class
    try:
        yield
    finally:
        obj.__class__ = old_class
