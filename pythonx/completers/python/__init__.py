# -*- coding: utf-8 -*-

import json
import os

from completor import Completor

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'
    daemon = True
    trigger = (r'[_\w\)\]\}\'\"]+\.[_\w]*$|'
               r'^\s*@[_\w]*$|'
               r'^\s*from\s+[_\w\.]*(?:\s+import\s+(?:[_\w]*(?:,\s*)?)*)?|'
               r'^\s*import\s+(?:[_\w\.]*(?:,\s*)?)*')

    def format_cmd(self):
        return ['python', os.path.join(DIRNAME, 'python_jedi.py')]

    def parse(self, data):
        try:
            data = json.loads(data)
        except Exception:
            data = [{'word': data}]
        return data
