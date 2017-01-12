# -*- coding: utf-8 -*-

try:
    from pipes import quote
except ImportError:
    from shlex import quote

from completor import Completor, get_encoding
from completor.compat import to_bytes

import platform

class Racer(Completor):
    filetype = 'rust'
    daemon = True
    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*)$'

    def format_cmd(self):
        binary = self.get_option('completor_racer_binary') or 'racer'
        return [binary, 'daemon']

    def request(self):
        line, col = self.cursor
        is_windows = platform.system() == "Windows"
        filename = self.filename if is_windows else quote(self.filename)
        tempname = self.tempname if is_windows else quote(self.tempname)
        return ' '.join(['complete', str(line), str(col),
                         filename, tempname])

    def message_ended(self, msg):
        return msg == 'END'

    # items: list of bytes
    def parse(self, items):
        input_data = to_bytes(self.input_data, get_encoding())

        completions = []
        for item in items:
            if not item.startswith(b'MATCH'):
                continue

            parts = item.split(b',')
            if len(parts) < 6:
                continue

            name = parts[0][6:]
            kind = parts[4].lower()
            spec = b'mod' if kind == b'module' else b', '.join(parts[5:])
            if spec.startswith(b'pub '):
                spec = spec[4:]

            if spec.startswith(input_data):
                continue

            completions.append({
                'word': name,
                'menu': spec,
                'dup': 0
            })
        return completions
