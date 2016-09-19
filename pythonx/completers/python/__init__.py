# -*- coding: utf-8 -*-

import os
import json

from completor import Completor

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'

    def format_cmd(self):
        line, col = self.cursor
        return ['python', os.path.join(DIRNAME, 'python_jedi.py'),
                '-l', str(line), '-c', str(col), '-n', self.filename,
                '-d', self.input_data,
                self.tempname]

    def parse(self, items):
        res = []
        for item in items:
            try:
                res.append(json.loads(item))
            except Exception:
                res.append({'word': item})
        return res
