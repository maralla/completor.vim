# -*- coding: utf-8 -*-

import os
import re
import logging
from completor import Completor

from .utils import test_subseq, LIMIT


logger = logging.getLogger('completor')
DSN_PAT = re.compile('\w+:(//?[^\s]*)?')


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
        if entry.startswith('.'):
            score += 1000
        entry = {
            'word': entry,
            'abbr': abbr,
            'menu': '[F]',
        }
        entries.append((entry, score))
        if len(entries) >= LIMIT:
            break
    entries.sort(key=lambda x: x[1])
    return entries


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
        """
        :param base: type unicode
        """
        logger.info('start filename parse: %s', base)
        pat = list(DSN_PAT.finditer(base))
        if pat:
            base = base[pat[-1].end():]

        try:
            match = self.trigger.search(base)
        except TypeError as e:
            logger.exception(e)
            match = None

        if not match:
            logger.info('no matches')
            return []
        try:
            items = find(self.current_directory, match.group())
        except Exception as e:
            logger.exception(e)
            return []
        logger.info('completions: %s', items)
        return [item[0] for item in items]
