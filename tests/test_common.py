# -*- coding: utf-8 -*-

import completor
from completor.compat import to_unicode

from completers.common import Common  # noqa


class Buffer(list):
    def __init__(self, number):
        self.number = number
        self.valid = 1


def test_get_completions(vim_mod):
    common = completor.get('common')

    vim_mod.current.buffer.number = 1
    vim_mod.current.window.cursor = (1, 2)
    vim_mod.vars = {}

    buffer = Buffer(1)
    with open(__file__) as f:
        buffer[:] = f.read().split('\n')

    vim_mod.buffers = [buffer]
    assert common.get_completions('urt') == [
        {'menu': '[snip] mock snips', 'word': 'ultisnips_trigger'},
        {'menu': '[ID]', 'word': 'current'}
    ]

    vim_mod.vars = {'completor_disable_ultisnips': 1}
    assert common.get_completions('urt') == [
        {'menu': '[ID]', 'word': 'current'}]

    vim_mod.vars = {'completor_disable_buffer': 1}
    assert common.get_completions('urt') == [
        {'menu': '[snip] mock snips', 'word': 'ultisnips_trigger'}]


def test_unicode(vim_mod):
    buffer = Buffer(1)
    with open('./tests/test.txt') as f:
        buffer[:] = f.read().split('\n')
    vim_mod.buffers = [buffer]
    vim_mod.current.buffer.number = 1
    vim_mod.current.window.cursor = (1, 14)

    buf = completor.get('buffer')
    buf.input_data = to_unicode('hello pielęgn', 'utf-8')
    assert buf.start_column() == 6
    assert buf.get_completions(b'piel\xc4\x99gn') == [
        {'menu': '[ID]', 'word': to_unicode('pielęgniarką', 'utf-8')},
        {'menu': '[ID]', 'word': to_unicode('pielęgniarkach', 'utf-8')}
    ]
