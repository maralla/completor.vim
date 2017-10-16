# -*- coding: utf-8 -*-

import json
import os
import vim
import logging

from completor import Completor
from completor.compat import to_unicode

DIRNAME = os.path.dirname(__file__)
logger = logging.getLogger('completor')


class Jedi(Completor):
    filetype = 'python'
    trigger = (r'\w{3,}$|'
               r'[\w\)\]\}\'\"]+\.\w*$|'
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

    on_doc = on_definition

    def on_complete(self, data):
        try:
            data = to_unicode(data[0], 'utf-8') \
                .replace('\\u', '\\\\\\u') \
                .replace('\\U', '\\\\\\U')
            items = json.loads(data)
            logger.info('%r => %r', self.input_data, items)
            return [i for i in json.loads(data)
                    if not self.input_data.endswith(i['word'])]
        except Exception as e:
            logger.exception(e)
            return []

    def on_signature(self, data):
        return json.loads(data[0])
