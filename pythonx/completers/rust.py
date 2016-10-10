# -*- coding: utf-8 -*-

from completor import Completor


class Racer(Completor):
    filetype = 'rust'

    def format_cmd(self):
        line, col = self.cursor
        return ['racer', 'complete', line, col, self.filename, self.tempname]

    def parse(self, items):
        completions = []
        for item in items:
            if not item.startswith('MATCH'):
                continue

            parts = item.split(',')
            name = parts[0][6:]
            spec = ', '.join(parts[5:])

            completions.append({
                'word': name,
                'menu': spec,
                'dup': 0
            })
        return completions
