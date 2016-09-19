# -*- coding: utf-8 -*-

import importlib
import re
import vim

current_completer = None


class Meta(type):
    def __init__(cls, name, bases, attrs):
        if name not in ('Completor', 'Base'):
            Completor._registry[cls.filetype] = cls()

        return super(Meta, cls).__init__(name, bases, attrs)

Base = Meta('Base', (object,), {})


class Unusable(object):
    def __get__(self, inst, owner):
        raise RuntimeError('unusable')


class Completor(Base):
    _registry = {}
    _commons = None

    filetype = Unusable()
    name = Unusable()
    pattern = None
    common = False

    def __init__(self):
        self.input_data = ''

    def commons(cls):
        if cls._commons is None:
            cls._commons = tuple(c for c in cls._registry.values()
                                 if c.common)
        return cls._commons

    @property
    def tempname(self):
        return vim.eval('completor#utils#tempname()')

    @property
    def filename(self):
        return vim.current.buffer.name

    @property
    def cursor(self):
        return vim.current.window.cursor

    def match(self, input_data):
        if self.pattern is None:
            return True

        return bool(re.search(self.pattern, input_data, re.X))

_completor = Completor()


def _load(ft, input_data):
    commons = _completor.commons()
    for c in commons:
        if c.match(input_data):
            return c

    if not ft:
        return None

    if ft not in _completor._registry:
        try:
            importlib.import_module("completers.{}".format(ft))
        except ImportError:
            return None
    return _completor._registry.get(ft)


def load_completer(ft, input_data):
    completer = _load(ft, input_data)
    if completer is not None:
        completer.input_data = input_data
    return completer
