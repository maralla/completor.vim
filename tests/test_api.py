import json
from completor import api

from . import Buffer


def test_get_completer(vim_mod):
    vim_mod.var_map['a:'] = {'ft': 'common', 'inputted': 'os.'}
    assert api.get_completer() == ['', 'common', False, True]


def test_get_completions(vim_mod):
    vim_mod.var_map['a:'] = {
        'ft': 'common',
        'inputted': 'os.',
        'msg': []
    }
    api.get_completer()
    assert api.get_completions() == []


def test_get_start_column(vim_mod):
    vim_mod.current.window.cursor = (1, 2)
    assert api.get_start_column() == 3


def test_get_daemon_request(vim_mod):
    vim_mod.current.window.cursor = (1, 2)
    vim_mod.current.buffer = Buffer(1, name='test')
    assert json.loads(api.get_daemon_request()) == {
        "content": "",
        "line": 0,
        "col": 3,
        "filename": "test"
    }


def test_is_message_end(vim_mod):
    vim_mod.var_map['a:'] = {'msg': ''}
    assert api.is_message_end()


def test_fallback_to_common():
    assert not api.fallback_to_common()
