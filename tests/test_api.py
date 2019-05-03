import json
from completor import api


def test_get_completer(vim_mod):
    vim_mod.var_map['a:'] = {'ft': 'common', 'inputted': 'os.'}
    assert api.get_completer() == {
        'is_sync': True,
        'ftype': 'common',
        'cmd': '',
        'is_daemon': False
    }


def test_on_data(vim_mod):
    vim_mod.var_map['a:'] = {
        'ft': b'common',
        'inputted': b'os.',
        'msg': [],
        'action': b'complete'
    }
    api.get_completer()
    assert api.on_data() == []


def test_get_start_column(vim_mod):
    vim_mod.current.window.cursor = (1, 2)
    assert api.get_start_column() == 3


def test_prepare_request(vim_mod, create_buffer):
    vim_mod.var_map['a:'] = {
        'action': b'complete',
        'args': {},
    }
    vim_mod.current.window.cursor = (1, 2)
    vim_mod.current.buffer = create_buffer(1, name='test')
    assert json.loads(api.gen_request()) == {
        "content": "",
        "line": 0,
        "col": 3,
        "filename": "test"
    }


def test_is_message_end(vim_mod):
    vim_mod.var_map['a:'] = {'msg': ''}
    assert api.is_message_end()
