# -*- coding: utf-8 -*-

try:
    from pipes import quote
except ImportError:
    from shlex import quote

from completor import Completor, get_encoding, vim
from completor.compat import to_bytes

ACTION_MAP = {
    b'complete': 'complete',
    b'definition': 'find-definition',
    b'doc': 'complete-with-snippet'
}


class Racer(Completor):
    filetype = 'rust'
    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*)$'

    def _format(self):
        rustfmt = self.get_option('rust_rustfmt_binary') or 'rustfmt'
        return [rustfmt, self.filename]

    def get_cmd_info(self, action):
        if action == b'format':
            return vim.Dictionary(
                cmd=self._format(),
                is_daemon=False,
                ftype=self.filetype,
                is_sync=False
            )
        binary = self.get_option('racer_binary') or 'racer'
        return vim.Dictionary(
            cmd=[binary, 'daemon'],
            is_daemon=True,
            ftype=self.filetype,
            is_sync=False
        )

    def prepare_request(self, action):
        line, _ = self.cursor
        col = len(self.input_data)
        if action == b'doc':
            col += 1
        action = ACTION_MAP.get(action)
        if not action:
            return ''
        return ' '.join([action, str(line), str(col),
                         quote(self.filename), quote(self.tempname)])

    def is_message_end(self, msg):
        return msg == b'END'

    def on_definition(self, items):
        ret = []
        for item in items:
            if not item.startswith(b'MATCH'):
                continue
            parts = item.split(b',')
            if len(parts) < 4:
                continue
            ret.append({'filename': parts[3], 'lnum': int(parts[1]),
                        'col': int(parts[2]) + 1, 'name': parts[0]})
        return ret

    def on_doc(self, items):
        ret = []
        for item in items:
            if not item.startswith(b'MATCH'):
                continue
            parts = item.split(b';', 7)
            if len(parts) < 8:
                continue
            doc = parts[-1].replace(b'\\n', b'\n').replace(b"\\'", b"'").\
                replace(b'\;', b';').replace(b'\\"', b'"').strip(b'"')
            if doc:
                ret.append(doc)
        return ret

    # items: list of bytes
    def on_complete(self, items):
        if self.is_comment_or_string() or '///' in self.input_data:
            return []

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
