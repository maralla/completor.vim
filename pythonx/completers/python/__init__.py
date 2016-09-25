# -*- coding: utf-8 -*-

import os
import json

from completor import Completor

DIRNAME = os.path.dirname(__file__)


class Jedi(Completor):
    filetype = 'python'
    daemon = True

    def format_cmd(self):
        return ['python', os.path.join(DIRNAME, 'python_jedi.py')]

    def parse(self, data):
        try:
            data = json.loads(data)
        except Exception:
            data = [{'word': data}]
        return data
