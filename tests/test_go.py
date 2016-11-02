# -*- coding: utf-8 -*-

import mock
import completor
from completor.compat import to_unicode
from completers.go import Go  # noqa


def test_format_cmd(vim_mod):
    vim_mod.funcs['line2byte'] = mock.Mock(return_value=20)
    vim_mod.funcs['completor#utils#tempname'] = mock.Mock(
        return_value=b'/tmp/vJBio2A/2.vim')
    vim_mod.current.window.cursor = (1, 5)

    go = completor.get('go')
    go.input_data = to_unicode('self.', 'utf-8')
    assert go.format_cmd() == [
        'gocode', '-f=csv', '--in=/tmp/vJBio2A/2.vim', 'autocomplete', 24]


def test_parse():
    data = [
        b'func,,Errorf,,func(format string, a ...interface{}) error',
        b'func,,Fprint,,func(w io.Writer, a ...interface{}) (n int, err error)',  # noqa
    ]
    go = completor.get('go')
    assert go.parse(data) == [{
        'word': b'Errorf',
        'menu': b'func(format string, a ...interface{}) error'
    }, {
        'word': b'Fprint',
        'menu': b'func(w io.Writer, a ...interface{}) (n int, err error)'
    }]
