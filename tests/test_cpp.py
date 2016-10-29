# -*- coding: utf-8 -*-

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
