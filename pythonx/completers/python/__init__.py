# -*- coding: utf-8 -*-

import json
import os

from completor import Completor

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'
    daemon = True
    trigger = (r'[\w\)\]\}\'\"]+\.\w*$|'
               r'^\s*@\w*$|'
               r'^\s*from\s+[\w\.]*(?:\s+import\s+(?:\w*(?:,\s*)?)*)?|'
               r'^\s*import\s+(?:[\w\.]*(?:,\s*)?)*')

    def format_cmd(self):
        return ['python', os.path.join(DIRNAME, 'python_jedi.py')]

    def parse(self, data):
        try:
            return json.loads(data)
        except Exception:
            return []
