# -*- coding: utf-8 -*-

import mock
import completor
from completor.compat import to_unicode
from completers.cpp import Clang  # noqa


def test_parse(vim_mod):
    items = [
        b'COMPLETION: pclose : [#int#]pclose(<#FILE *#>)',
        b'COMPLETION: hello : [#int#]hello',
        b'COMPLETION: b : [#int#]b',
        b'COMPLETION: Pattern: fake hello',
    ]

    cpp = completor.get('cpp')
    cpp.input_data = to_unicode('b->', 'utf-8')
    assert cpp.get_completions(items) == [
        {'dup': 1, 'menu': b'int pclose(FILE *)', 'word': b'pclose'},
        {'dup': 1, 'menu': b'int hello', 'word': b'hello'},
        {'dup': 1, 'menu': b'int b', 'word': b'b'},
        {'dup': 1, 'menu': b'hello', 'word': b'fake'}
    ]


def test_format_cmd(vim_mod):
    vim_mod.funcs['expand'] = mock.Mock(return_value=b'/tmp/vJBio2A')
    vim_mod.funcs['completor#utils#tempname'] = mock.Mock(
        return_value=b'/tmp/vJBio2A/2.cpp')
    vim_mod.current.window.cursor = (1, 5)
    cpp = completor.get('cpp')
    cpp.input_data = to_unicode('self.', 'utf-8')
    assert cpp.format_cmd() == [
        'clang', '-fsyntax-only', '-I', '/tmp/vJBio2A',
        '-Xclang', '-code-completion-macros',
        '-Xclang', '-code-completion-at=/tmp/vJBio2A/2.cpp:1:6',
        '/tmp/vJBio2A/2.cpp']
