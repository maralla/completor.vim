# -*- coding: utf-8 -*-

import re
from completor import Completor


word_patten = re.compile('\w+$')
trigger = re.compile('(\.|->|#|::)\s*(\w*)$')


class Clang(Completor):
    filetype = 'cpp'

    args_file = '.clang_completer'

    def format_cmd(self):
        row, col = self.cursor
        tempfile = self.tempname

        match = trigger.search(self.input_data)
        if match:
            start, end = match.span()
            sign, _ = match.groups()
            col = start + (2 if sign in ('->', '::') else 1)
        elif not word_patten.search(self.input_data):
            return []

        args = [
            self.get_option('completor_clang_binary') or 'clang',
            '-fsyntax-only',
            '-I{}'.format(self.current_directory),
        ]
        args.extend(self.parse_config(self.args_file))
        args.extend([
            '-Xclang',
            '-code-completion-macros',
            '-Xclang',
            '-code-completion-at={}:{}:{}'.format(tempfile, row, col + 1),
            tempfile
        ])
        return args

    def parse(self, items):
        match = trigger.search(self.input_data)
        if match:
            _, prefix = match.groups()
        else:
            match = word_patten.search(self.input_data)
            if not match:
                return []
            prefix = match.group()

        res = []
        for item in items:
            if not item.startswith('COMPLETION:'):
                continue

            parts = [e.strip() for e in item.split(':')]
            if len(parts) < 2 or not parts[1].startswith(prefix):
                continue

            data = {'word': parts[1], 'dup': 1}
            if len(parts) > 2:
                if parts[1] == 'Pattern':
                    subparts = parts[2].split(' ', 1)
                    data['word'] = subparts[0]
                    if len(subparts) > 1:
                        data['menu'] = subparts[1]
                else:
                    data['menu'] = ':'.join(parts[2:])
            res.append(data)
        return res
