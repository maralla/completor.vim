# -*- coding: utf-8 -*-

import mock
from completor import Completor, load_completer, get


class HelloCompleter(Completor):
    filetype = 'hello'


def test_disabled(vim_mod):
    com = HelloCompleter()
    vim_mod.vars = {'completor_disable_hello': 1}
    assert com.disabled
    vim_mod.vars = {'completor_disable_hello': [b'hello']}
    com.ft = 'hello'
    assert com.disabled
    vim_mod.vars = {}
    assert not com.disabled


def test_load(vim_mod, monkeypatch):
    from completor import _completor
    vim_mod.eval = mock.Mock(return_value={})
    vim_mod.vars = {}

    with mock.patch.object(_completor, '_type_map',
                           {b'python.django': b'python'}):
        assert load_completer('', '/etc') is None
        assert load_completer('hello', '') is None
        assert get('python') is None
        c = load_completer('python', 'os.')
        assert c.input_data == 'os.'
        assert get('python') is c

        c = load_completer('python', '#')
        assert c is get('common')

        c = load_completer('python.django', 'os.')
        assert c is get('python')

        vim_mod.current.buffer.options = {
            'omnifunc': b'csscomplete#CompleteCSS'}
        vim_mod.vars = {
            'completor_css_omni_trigger': b'([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$'
        }
        assert load_completer('css', 'text') is get('omni')
