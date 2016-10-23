# -*- coding: utf-8 -*-

from completor import Completor


class HelloCompleter(Completor):
    filetype = 'hello'


class List(object):
    pass


def test_disabled(vim_mod):
    vim_mod.List = List
    vim_mod.current.buffer.options = {'ft': 'hello'}
    com = HelloCompleter()
    vim_mod.vars = {'completor_disable_hello': 1}
    assert com.disabled
    vim_mod.vars = {'completor_disable_hello': ['hello']}
    assert com.disabled
    vim_mod.vars = {}
    assert not com.disabled
