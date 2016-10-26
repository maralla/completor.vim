# -*- coding: utf-8 -*-

from completor import Completor


class Racer(Completor):
    filetype = 'rust'

    trigger = r'(?:\w{3,}\w*|\.\w*|::\w*)$'

    def format_cmd(self):
        line, col = self.cursor
        binary = self.get_option('completor_racer_binary') or 'racer'
        return [binary, 'complete', str(line), str(col), self.filename,
                self.tempname]

    def parse(self, items):
        completions = []
        for item in items:
            if not item.startswith('MATCH'):
                continue

            parts = item.split(',')
            name = parts[0][6:]

            kind = parts[4].lower()
            spec = 'mod' if kind == 'module' else ', '.join(parts[5:])
            if spec.startswith('pub '):
                spec = spec[4:]

            completions.append({
                'word': name,
                'menu': spec,
                'dup': 0
            })
        return completions
