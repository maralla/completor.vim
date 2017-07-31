# -*- coding: utf-8 -*-

import json
import os
import vim

from completor import Completor
from completor.compat import to_unicode

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'
    trigger = (r'[\w\)\]\}\'\"]+\.\w*$|'
               r'^\s*@\w*$|'
               r'^\s*from\s+[\w\.]*(?:\s+import\s+(?:\w*(?:,\s*)?)*)?|'
               r'^\s*import\s+(?:[\w\.]*(?:,\s*)?)*')

    def get_cmd_info(self, action):
        binary = self.get_option('python_binary') or 'python'
        cmd = [binary, os.path.join(DIRNAME, 'python_jedi.py')]
        return vim.Dictionary(
            cmd=cmd,
            ftype=self.filetype,
            is_daemon=True,
            is_sync=False,
        )

    def prepare_request(self, action):
        line, col = self.cursor
        return json.dumps({
            'action': action.decode('ascii'),
            'line': line - 1,
            'col': col,
            'filename': self.filename,
            'content': '\n'.join(vim.current.buffer[:])
        })

    def on_definition(self, data):
        return json.loads(data[0])

    def on_complete(self, data):
        try:
            data = to_unicode(data[0], 'utf-8').replace('\\u', '\\\\u')
            return json.loads(data)
        except Exception:
            return []
