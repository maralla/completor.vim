# -*- coding: utf-8 -*-

import mock
import pytest
import completor
from completers.go import Go  # noqa


class TestGetCmdInfo(object):
    expected = {
        b'complete': {
            'is_sync': False,
            'input_content': 'package\nmain',
            'cmd': [
                'gocode', '-f=csv', 'autocomplete',
                '/home/vagrant/bench.vim', 24
            ],
            'ftype': 'go',
            'is_daemon': False,
        },
        b'doc': {
            'is_sync': False,
            'cmd': ['gogetdoc', '-modified', '-json', '-pos',
                    '/home/vagrant/bench.vim:#24'],
            'ftype': 'go',
            'is_daemon': False,
            'input_content': '/home/vagrant/bench.vim\n12\npackage\nmain'
        }
    }

    @pytest.mark.parametrize('action', [b'complete', b'doc'])
    def test_get_cmd_info(self, vim_mod, create_buffer, action):
        vim_mod.funcs['line2byte'] = mock.Mock(return_value=20)
        vim_mod.current.buffer = buf = create_buffer(1)
        vim_mod.current.buffer.name = '/home/vagrant/bench.vim'
        vim_mod.current.window.cursor = (1, 5)
        buf[:] = ['package', 'main']

        go = completor.get('go')
        info = go.get_cmd_info(action)
        assert info == self.expected[action]


def test_parse():
    data = [
        b'func,,Errorf,,func(format string, a ...interface{}) error',
        b'func,,Fprint,,func(w io.Writer, a ...interface{}) (n int, err error)',  # noqa
    ]
    go = completor.get('go')
    assert go.on_complete(data) == [{
        'word': b'Errorf',
        'menu': b'func(format string, a ...interface{}) error',
        'info': b'func(format string, a ...interface{}) error'
    }, {
        'word': b'Fprint',
        'menu': b'func(w io.Writer, a ...interface{}) (n int, err error)',
        'info': b'func(w io.Writer, a ...interface{}) (n int, err error)'
    }]


class TestDoc(object):
    data = [
        '{"name": "RuneCountInString", "import": "unicode/utf8", "pkg": '
        '"utf8", "decl": "func RuneCountInString(s string) (n int)", "doc": '
        '"RuneCountInString is like RuneCount but its input is a string.\\n", '
        '"pos": "/usr/local/Cellar/go/1.9/libexec/src/unicode/utf8/utf8.go:'
        '412:6"}'
    ]

    expected = {
        'on_doc': ['import "unicode/utf8"\n\nfunc RuneCountInString'
                   '(s string) (n int)\n\nRuneCountInString is like '
                   'RuneCount but its input is a string.\n'],
        'on_definition': [{
            'col': '6',
            'filename': '/usr/local/Cellar/go/1.9/libexec/src/unicode/utf8/utf8.go',  # noqa
            'lnum': '412', 'name': 'RuneCountInString'}]
    }

    @pytest.mark.parametrize('action', ['on_doc', 'on_definition'])
    def test_doc(self, action):
        go = completor.get('go')
        ret = getattr(go, action)(self.data)
        assert ret == self.expected[action]
