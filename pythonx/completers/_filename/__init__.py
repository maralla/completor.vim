# -*- coding: utf-8 -*-

import os
import re
from completor import Completor

DIRNAME = os.path.dirname(__file__)


class Filename(Completor):
    filetype = 'filename'

    common = True
    trigger = re.compile(r"""
        # Head part
        (?:
        # '/', './', '../', or '~'
        \.{0,2}/|~|

        # '$var/'
        \$[A-Za-z0-9{}_]+/
        )+

        # Tail part
        (?:
        # any alphanumeric, symbol or space literal
        [/a-zA-Z0-9(){}$ +_~.'"\x80-\xff-\[\]]|

        # skip any special symbols
        [^\x20-\x7E]|

        # backslash and 1 char after it
        \\.
        )*$""", re.U | re.X)

    def format_cmd(self):
        binary = self.get_option('completor_python_binary') or 'python'
        match = self.trigger.search(self.input_data)
        if not match:
            return []
        return [binary, os.path.join(DIRNAME, 'pathfinder.py'), match.group()]

    def parse(self, items):
        return [{'word': item, 'menu': '[F]', 'dup': 0} for item in items]
