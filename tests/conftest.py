# -*- coding: utf-8 -*-

import mock
import sys
import pytest


class VimError(Exception):
    pass


class List(object):
    pass


def vim_eval(expr):
    return vim_eval.expr_map.get(expr)

vim_eval.expr_map = {'&encoding': b'utf-8'}


def getbufvar(nr, var):
    return b''

funcs = {'getbufvar': getbufvar}


def vim_function(func):
    return funcs.get(func, lambda: None)


@pytest.fixture
def vim_mod():
    vim = sys.modules['vim']
    attrs = dict(vim.__dict__)
    vim.current = mock.Mock()
    vim.current.buffer.options = {'fileencoding': b'utf-8'}
    vim.List = List
    vim.error = VimError
    vim.eval = vim_eval
    vim.Function = vim_function
    vim.funcs = funcs
    yield vim
    vim.__dict__.clear()
    vim.__dict__.update(attrs)
