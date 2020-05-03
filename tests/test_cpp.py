# -*- coding: utf-8 -*-

import mock
import completor
import functools
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
    assert cpp.on_data(b'complete', items) == [
        {'offset': 3, 'dup': 1, 'menu': b'int pclose(FILE *)', 'word': b'pclose', 'abbr': b'pclose'},  # noqa
        {'offset': 3, 'dup': 1, 'menu': b'int hello', 'word': b'hello', 'abbr': b'hello'},  # noqa
        {'offset': 3, 'dup': 1, 'menu': b'int b', 'word': b'b', 'abbr': b'b'},  # noqa
        {'offset': 3, 'dup': 1, 'menu': b'fake hello', 'word': b'fake', 'abbr': b'fake'}  # noqa
    ]


def test_get_cmd_info(vim_mod):
    vim_mod.funcs['expand'] = mock.Mock(return_value=b'/tmp/vJBio2A')
    vim_mod.funcs['completor#utils#tempname'] = mock.Mock(
        return_value=b'/tmp/vJBio2A/2.cpp')
    vim_mod.current.window.cursor = (1, 5)
    cpp = completor.get('cpp')
    cpp.input_data = to_unicode('self.', 'utf-8')
    assert cpp.get_cmd_info(b'complete')['cmd'] == [
        'clang', '-fsyntax-only', '-I', '/tmp/vJBio2A',
        '-Xclang', '-code-completion-macros',
        '-Xclang', '-code-completion-at=/tmp/vJBio2A/2.cpp:1:6',
        '/tmp/vJBio2A/2.cpp']


def test_parse_ast_dump():
    from completers.cpp import parse_ast_dump, group, is_group
    data = [
        b'Dumping command:',
        b"ParmVarDecl 0x2a135e8 </usr/include/stdio.h:872:21, col:33> col:33 __command 'const char *'",  # noqa
        b'',
        b'Dumping command:',
        b'RecordDecl 0x2a25f40 parent 0x28abd60 </usr/include/sys/queue.h:213:2, corvus/src/command.h:178:22> col:22 struct command',  # noqa
        b'',
        b'Dumping command:',
        b'RecordDecl 0x2a264d0 prev 0x2a25f40 <corvus/src/command.h:189:1, line:245:1> line:189:8 struct command definition'  # noqa
    ]
    groups = list(group(data, functools.partial(is_group, 'command')))
    assert groups == [
        [b"ParmVarDecl 0x2a135e8 </usr/include/stdio.h:872:21, col:33> col:33 __command 'const char *'", b''],  # noqa
        [b'RecordDecl 0x2a25f40 parent 0x28abd60 </usr/include/sys/queue.h:213:2, corvus/src/command.h:178:22> col:22 struct command', b''],  # noqa
        [b'RecordDecl 0x2a264d0 prev 0x2a25f40 <corvus/src/command.h:189:1, line:245:1> line:189:8 struct command definition']]  # noqa
    info = parse_ast_dump(data, 'command', '   struct command', 12)
    assert info == [
        {
            'filename': 'corvus/src/command.h',
            'name': 'command',
            'lnum': 189,
            'text': 'struct command definition',
            'col': 8
        }]


def test_get_token_path():
    from completers.cpp import get_token_path
    r = get_token_path('    std::hello::world::yes', 19, 'world')
    assert r == 'std::hello::world'
