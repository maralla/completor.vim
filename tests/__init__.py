# -*- coding: utf-8 -*-

import mock
import sys

from copy import deepcopy


class Buffer(list):
    def __init__(self, number, name=''):
        self.name = name
        self.number = number
        self.valid = 1


class VimError(Exception):
    pass


class List(object):
    pass


class Vars(dict):
    def __set__(self, inst, value):
        if not value:
            inst._vars = deepcopy(self)
        inst._vars.update(value)

    def __get__(self, inst, owner):
        args = deepcopy(self)
        args.update(inst._vars)
        inst._vars = args
        return inst._vars


class Vim(object):
    List = List
    error = VimError

    vars = Vars(completor_min_chars=2)

    def __init__(self):
        self.reset()

    def reset(self):
        self._vars = {}
        self.var_map = {}
        self.eval_map = {'&encoding': b'utf-8'}
        self.current = mock.Mock()
        self.current.buffer.options = {'fileencoding': b'utf-8'}
        self.funcs = {
            'getbufvar': lambda nr, var: b'',
            'completor#utils#in_comment_or_string': lambda: 0
        }

    def eval(self, expr):
        return self.eval_map.get(expr)

    def bindeval(self, category):
        return self.var_map.get(category, {})

    def Function(self, func_name):
        return self.funcs.get(func_name)


class UltiSnips(object):
    def _snips(self, base, other):
        if base != 'urt':
            return []

        return [mock.Mock(
            trigger='ultisnips_trigger', description='mock snips')]

sys.path.append('./pythonx')
sys.modules['vim'] = Vim()
sys.modules['UltiSnips'] = mock.Mock(UltiSnips_Manager=UltiSnips())
