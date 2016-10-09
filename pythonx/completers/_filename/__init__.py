# -*- coding: utf-8 -*-

import os
from completor import Completor

from .utils import PATH_PATTERN

DIRNAME = os.path.dirname(__file__)


class Filename(Completor):
    filetype = 'filename'

    common = True
    name = 'python'
    trigger = PATH_PATTERN

    def format_cmd(self):
        return ['python', os.path.join(DIRNAME, 'pathfinder.py'),
                self.input_data]

    def parse(self, items):
        return [{'word': item, 'menu': '[F]', 'dup': 0} for item in items]
