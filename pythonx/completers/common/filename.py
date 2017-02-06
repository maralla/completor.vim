# -*- coding: utf-8 -*-

import os
import re
from completor import Completor

from .utils import test_subseq, LIMIT


def find(current_dir, input_data):
    path_dir = os.path.expanduser(os.path.expandvars(input_data))
    if not path_dir:
        return []

    dirname, basename = os.path.split(path_dir)
    if not dirname:
        dirname = '.'

    if not os.path.isabs(dirname):
        dirname = os.path.join(current_dir, dirname)

    entries = []
    for entry in os.listdir(dirname):
        score = test_subseq(basename, entry)
        if score is None:
            continue

        abbr = ''
        if os.path.isdir(os.path.join(dirname, entry)):
            abbr = ''.join([entry, os.sep])
        entry = {
            'word': entry,
            'abbr': abbr,
            'menu': '[F]',
        }
        entries.append((entry, score))
    entries.sort(key=lambda x: x[1])
    return entries[:LIMIT]


class Filename(Completor):
    filetype = 'filename'

    sync = True
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

    ident = r"""[a-zA-Z0-9(){}$ +_~.'"\x80-\xff-\[\]]*"""

    def parse(self, base):
        match = self.trigger.search(base)
        if not match:
            return []
        try:
            items = find(self.current_directory, match.group())
        except Exception:
            return []
        return [item[0] for item in items]
