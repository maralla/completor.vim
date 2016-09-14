# -*- coding: utf-8 -*-

import importlib
import vim


class Meta(type):
    def __init__(cls, name, bases, attrs):
        if name not in ('Completor', 'Base'):
            Completor._registry[cls.__filetype__] = cls()

        return super(Meta, cls).__init__(name, bases, attrs)

Base = Meta('Base', (object,), {})


class Unusable(object):
    def __get__(self, inst, owner):
        raise RuntimeError('unusable')


class Completor(Base):
    _registry = {}

    __filetype__ = Unusable()
    name = Unusable()

    @property
    def tempname(self):
        return vim.eval('completor#utils#tempname()')

    @property
    def filename(self):
        return vim.current.buffer.name

    @property
    def cursor(self):
        return vim.current.window.cursor

_completor = Completor()


def load_completer(ft):
    if not ft:
        return None

    if ft not in _completor._registry:
        try:
            importlib.import_module("completers.{}".format(ft))
        except ImportError:
            return None
    return _completor._registry[ft]
