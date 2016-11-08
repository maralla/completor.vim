# -*- coding: utf-8 -*-

import os
import re
from completor import Completor

from .utils import test_subseq, LIMIT, subseq_binary

IDENT = r"""[a-zA-Z0-9(){}$ +_~.'"\x80-\xff-\[\]]*"""
TRIGGER = re.compile(r"""
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


def normalize(path):
    return os.path.expanduser(os.path.expandvars(path))


def find(input_data):
    path_dir = normalize(input_data)
    if not path_dir:
        return []

    dirname, basename = os.path.split(path_dir)
    if not dirname:
        dirname = '.'

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
    trigger = TRIGGER
    ident = IDENT

    def format_cmd(self):
        return [subseq_binary()]

    def request(self):
        match = self.trigger.search(self.input_data)
        if not match:
            return ''
        return ''.join(['FIL', normalize(match.group())])

    def daemon_response(self, items):
        res = []
        for item in items:
            if not item or item.startswith(b'Err:'):
                continue
            for i in item.split(b'||'):
                word, sign = i.split(b',,')
                res.append({'word': word, 'menu': '[{}]'.format(sign.upper())})
        return res

    def parse(self, base):
        if self.daemon:
            return self.daemon_response(base)
        else:
            match = self.trigger.search(base)
            if not match:
                return []
            try:
                items = find(match.group())
            except Exception:
                return []
            return [item[0] for item in items]
