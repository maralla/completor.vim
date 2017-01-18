# -*- coding: utf-8 -*-

import mock
import completor
from completor.compat import to_unicode

from completers.common import Common  # noqa

from . import Buffer


def test_get_completions(vim_mod):
    common = completor.get('common')

    vim_mod.current.buffer.number = 1
    vim_mod.current.window.cursor = (1, 2)

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

    vim_mod.vars = {
        'completor_disable_buffer': 1,
        'completor_disable_ultisnips': 0
    }

    assert common.get_completions('urt') == [
        {'menu': '[snip] mock snips', 'word': 'ultisnips_trigger'}]


def test_unicode(vim_mod):
    buffer = Buffer(1)
    with open('./tests/test.txt') as f:
        buffer[:] = f.read().split('\n')
    vim_mod.buffers = [buffer]
    vim_mod.current.buffer.number = 1
    vim_mod.current.window.cursor = (1, 16)

    buf = completor.get('buffer')
    buf.input_data = to_unicode('pielę pielęgn', 'utf-8')
    assert buf.start_column() == 7
    assert buf.get_completions(b'piel\xc4\x99gn') == [
        {'menu': '[ID]', 'word': to_unicode('pielęgniarką', 'utf-8')},
        {'menu': '[ID]', 'word': to_unicode('pielęgniarkach', 'utf-8')}
    ]


def test_min_chars(vim_mod, monkeypatch):
    vim_mod.vars = {'completor_min_chars': 3}
    common = completor.get('common')
    mock_buffer_parse = mock.Mock(return_value=['hello'])
    monkeypatch.setattr(completor.get('buffer'), 'parse', mock_buffer_parse)

    mock_snips_parse = mock.Mock(return_value=['snips'])
    monkeypatch.setattr(completor.get('ultisnips'), 'parse', mock_snips_parse)

    assert common.get_completions('he') == []
    mock_buffer_parse.assert_not_called()
    mock_snips_parse.assert_not_called()

    assert common.get_completions('hello') == ['snips', 'hello']
    mock_buffer_parse.assert_called_with('hello')
    mock_snips_parse.assert_called_with('hello')
