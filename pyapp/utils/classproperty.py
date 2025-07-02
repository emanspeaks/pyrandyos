# see: https://stackoverflow.com/a/5191224/13230486

from collections.abc import Callable


class ClassPropertyDescriptor:
    def __init__(self, fget: Callable, fset: Callable = None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")

        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func: Callable):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func: Callable):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)
