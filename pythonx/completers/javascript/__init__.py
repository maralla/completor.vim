# -*- coding: utf-8 -*-

import json
import os.path

from completor import Completor

dirname = os.path.dirname(__file__)


class Tern(Completor):
    filetype = 'javascript'
    daemon = True

    def format_cmd(self):
        return ['node', os.path.join(dirname, 'tern_wrapper.js')]

    def parse(self, data):
        try:
            return json.loads(data)
        except Exception:
            return []
