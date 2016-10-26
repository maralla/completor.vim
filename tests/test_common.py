# -*- coding: utf-8 -*-

import completor

from completers.common import Common  # noqa


class Buffer(list):
    def __init__(self, number):
        self.number = number
        self.valid = 1


def test_parse(vim_mod):
    common = completor.get('common')

    vim_mod.current.buffer.number = 1
    vim_mod.current.window.cursor = (1, 2)
    vim_mod.vars = {}

    buffer = Buffer(1)
    with open(__file__) as f:
        buffer[:] = f.read().split('\n')

    vim_mod.buffers = [buffer]
    assert common.parse('urt') == [
        {'menu': '[snip] mock snips', 'word': 'ultisnips_trigger'},
        {'menu': '[ID]', 'word': 'current'}
    ]

    vim_mod.vars = {'completor_disable_ultisnips': 1}
    assert common.parse('urt') == [{'menu': '[ID]', 'word': 'current'}]

    vim_mod.vars = {'completor_disable_buffer': 1}
    assert common.parse('urt') == [
        {'menu': '[snip] mock snips', 'word': 'ultisnips_trigger'}]
