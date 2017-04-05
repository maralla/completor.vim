# -*- coding: utf-8 -*-

import re
import os
from completor import Completor
from completor.compat import to_bytes


word_patten = re.compile('\w+$')
trigger = re.compile('(\.|->|#|::)\s*(\w*)$')


def sanitize(menu):
    if not menu:
        return menu

    # type
    menu = menu.replace(b'[#', b'').replace(b'#]', b' ')
    # argument
    menu = menu.replace(b'<#', b'').replace(b'#>', b'')
    return menu


class Clang(Completor):
    filetype = 'cpp'

    args_file = '.clang_complete'

    def format_cmd(self):
        row, col = self.cursor
        tempfile = self.tempname

        match = trigger.search(self.input_data)
        if match:
            start, _ = match.span()
            sign, _ = match.groups()
            col = start + (2 if sign in ('->', '::') else 1)
        elif not word_patten.search(self.input_data):
            return []

        args = [
            self.get_option('clang_binary') or 'clang',
            '-fsyntax-only',
            '-I',
            self.current_directory,
        ]
        args.extend(self.parse_config(self.args_file))
        complatfile = tempfile
        if os.getenv('MSYSTEM') is not None:
            cmd = 'cygpath -a -w {}'.format(complatfile)
            complatfile = os.popen(cmd).read()
            complatfile = complatfile.strip().replace('\\', '\\\\')
        args.extend([
            '-Xclang',
            '-code-completion-macros',
            '-Xclang',
            '-code-completion-at={}:{}:{}'.format(complatfile, row, col + 1),
            tempfile
        ])
        return args

    # items: list of bytes
    def parse(self, items):
        match = trigger.search(self.input_data)
        if match:
            _, prefix = match.groups()
        else:
            match = word_patten.search(self.input_data)
            if not match:
                return []
            prefix = match.group()
        prefix = to_bytes(prefix)

        res = []
        for item in items:
            if not item.startswith(b'COMPLETION:'):
                continue

            parts = [e.strip() for e in item.split(b':')]
            if len(parts) < 2 or not parts[1].startswith(prefix):
                continue

            data = {'word': parts[1], 'dup': 1, 'menu': ''}
            if len(parts) > 2:
                if parts[1] == b'Pattern':
                    subparts = parts[2].split(b' ', 1)
                    data['word'] = subparts[0]
                    if len(subparts) > 1:
                        data['menu'] = subparts[1]
                else:
                    data['menu'] = b':'.join(parts[2:])
            data['menu'] = sanitize(data['menu'])
            res.append(data)
        return res
