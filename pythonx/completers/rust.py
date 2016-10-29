# -*- coding: utf-8 -*-

from completor import Completor


class Racer(Completor):
    filetype = 'rust'

    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*)$'

    def format_cmd(self):
        line, col = self.cursor
        binary = self.get_option('completor_racer_binary') or 'racer'
        return [binary, 'complete', str(line), str(col), self.filename,
                self.tempname]

    # items: list of bytes
    def parse(self, items):
        completions = []
        for item in items:
            if not item.startswith(b'MATCH'):
                continue

            parts = item.split(b',')
            name = parts[0][6:]

            kind = parts[4].lower()
            spec = b'mod' if kind == b'module' else b', '.join(parts[5:])
            if spec.startswith(b'pub '):
                spec = spec[4:]

            completions.append({
                'word': name,
                'menu': spec,
                'dup': 0
            })
        return completions
