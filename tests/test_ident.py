# -*- coding: utf-8 -*-

from completor.ident import start_column


def test_start_column(vim_mod):
    vim_mod.current.window.cursor = (1, 4)
    vim_mod.current.line = 'if hello'

    assert start_column(b'python') == 3
