# -*- coding: utf-8 -*-

import json
import os
import re

from completor import Completor

DIRNAME = os.path.dirname(__file__)
trigger = re.compile('(\w|\.)+$')


class Jedi(Completor):
    filetype = 'python'
    daemon = True

    def format_cmd(self):
        input_data = self.input_data.strip()
        if not input_data or not trigger.search(input_data):
            return []

        return ['python', os.path.join(DIRNAME, 'python_jedi.py')]

    def parse(self, data):
        try:
            data = json.loads(data)
        except Exception:
            data = [{'word': data}]
        return data
