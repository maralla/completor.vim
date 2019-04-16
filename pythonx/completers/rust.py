# -*- coding: utf-8 -*-

try:
    from pipes import quote
except ImportError:
    from shlex import quote

import logging
from io import BytesIO
from completor import Completor, get_encoding, vim
from completor.compat import to_bytes

ACTION_MAP = {
    b'complete': 'complete',
    b'definition': 'find-definition',
    b'doc': 'complete-with-snippet'
}

logger = logging.getLogger('completor')


class Racer(Completor):
    filetype = 'rust'
    trigger = r'(?:\w{2,}\w*|\.\w*|::\w*)$'

    def __init__(self, *args, **kwargs):
        Completor.__init__(self, *args, **kwargs)
        self.processed = []
        self.unprocessed = BytesIO()

    def reset_buffer(self):
        self.processed = []
        self.unprocessed = BytesIO()

    def get_cmd_info(self, action):
        binary = self.get_option('racer_binary') or 'racer'
        return vim.Dictionary(
            cmd=[binary, 'daemon'],
            is_daemon=True,
            ftype=self.filetype,
            is_sync=False
        )

    def prepare_request(self, action):
        self.reset_buffer()
        line, _ = self.cursor
        col = len(self.input_data)
        if action == b'doc':
            col += 1
        action = ACTION_MAP.get(action)
        if not action:
            return ''
        return ' '.join([action, str(line), str(col),
                         quote(self.filename), quote(self.tempname)]) + '\n'

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
            completions.append(vim.Dictionary(word=name, menu=spec, dup=0))
        return vim.List(completions)

    def on_stream(self, action, data):
        self.unprocessed.write(data)
        data = self.unprocessed.getvalue()
        items = data.split('\n')
        if not items:
            return
        if items[-1] == '':
            processed = items
            buf = BytesIO()
        else:
            processd = items[:-1]
            buf = BytesIO(items[-1])
        self.unprocessed = buf
        self.processed.extend(processed)
        if len(self.processed) > 2 and self.processed[-2].lower() == 'end':
            res = self.on_data(action, self.processed)
            self.reset_buffer()
            return res
