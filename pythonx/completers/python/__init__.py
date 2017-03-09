# -*- coding: utf-8 -*-

import json
import os

from completor import Completor
from completor.compat import to_unicode

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'
    daemon = True
    trigger = (r'[\w\)\]\}\'\"]+\.\w*$|'
               r'^\s*@\w*$|'
               r'^\s*from\s+[\w\.]*(?:\s+import\s+(?:\w*(?:,\s*)?)*)?|'
               r'^\s*import\s+(?:[\w\.]*(?:,\s*)?)*')

    def format_cmd(self):
        binary = self.get_option('python_binary') or 'python'
        return [binary, os.path.join(DIRNAME, 'python_jedi.py')]

    def parse(self, data):
        try:
            data = to_unicode(data[0], 'utf-8').replace('\\u', '\\\\u')
            return json.loads(data)
        except Exception:
            return []
