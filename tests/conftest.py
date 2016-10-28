# -*- coding: utf-8 -*-

import mock
import sys
import pytest


class VimError(Exception):
    pass


class List(object):
    pass


def vim_eval(expr):
    return vim_eval.data.get(expr)

vim_eval.data = {'&encoding': 'utf-8'}


def getbufvar(nr, var):
    return ''


def vim_function(func):
    return vim_function.funcs.get(func, lambda: None)

vim_function.funcs = {'getbufvar': getbufvar}


@pytest.fixture
def vim_mod():
    vim = sys.modules['vim']
    attrs = dict(vim.__dict__)
    vim.current = mock.Mock()
    vim.List = List
    vim.error = VimError
    vim.eval = vim_eval
    vim.Function = vim_function
    yield vim
    vim.__dict__.clear()
    vim.__dict__.update(attrs)
