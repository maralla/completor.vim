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
    vim_mod.eval = mock.Mock(return_value={})
    vim_mod.vars = {
        'completor_filetype_map': {
            b'python.django': b'python'
        }
    }
    assert get('python') is None
    c = load_completer(b'python', b'os.')
    assert c.input_data == 'os.'
    assert get('python') is c

    c = load_completer(b'python', b'#')
    assert c is get('common')

    c = load_completer(b'python.django', b'os.')
    assert c is get('python')

    vim_mod.current.buffer.options.update({
        'omnifunc': b'csscomplete#CompleteCSS'})
    vim_mod.vars = {
        'completor_css_omni_trigger': br'([\w-]+|@[\w-]*|[\w-]+:\s*[\w-]*)$'
    }
    assert load_completer(b'css', b'text') is get('omni')


def test_parse_config():
    h = HelloCompleter()
    args = h.parse_config('tests/test_config')
    assert args == ['-I/home/hello', '-x', '--std=c11', '-hello=world',
                    'abcd', '-a', '123']
    args = h.parse_config(['tests/invalid', 'tests/args',
                           'tests/tests_config'])
    assert args == ['-x', 'c', '-D/usr/lib/', '123']
