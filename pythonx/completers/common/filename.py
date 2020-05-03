# -*- coding: utf-8 -*-

import os
import re
import logging
import glob
import itertools
from completor import Completor, LIMIT

from .utils import test_subseq


logger = logging.getLogger('completor')
PAT = re.compile(r'(\w{2,}:(//?[^\s]*)?)|(</[^\s>]*>?)|(//)')
START_NO_DIRNAME = re.compile(r'^(\.{0,2}/|~/|[a-zA-Z]:/|\$)')


def gen_entry(pat, dirname, basename, offset):
    prefix = len(dirname)
    if os.path.dirname(dirname) != dirname:
        prefix += 1
    for fname in glob.iglob(pat):
        entry = fname[prefix:]
        score = test_subseq(basename, entry)
        if score is None:
            continue

        abbr = ''
        if os.path.isdir(os.path.join(dirname, entry)):
            abbr = ''.join([entry, os.sep])
        if entry.startswith('.'):
            score += 100000
        entry = {
            'word': entry,
            'abbr': abbr,
            'menu': '[F]',
            'offset': offset,
        }
        yield entry, score


def find(current_dir, input_data, offset):
    path_dir = os.path.expanduser(os.path.expandvars(input_data))
    if not path_dir:
        return []

    dirname, basename = os.path.split(path_dir)
    if not dirname:
        dirname = '.'

    if not os.path.isabs(dirname):
        dirname = os.path.join(current_dir, dirname)

    def _pat(p):
        return os.path.join(dirname, p)

    hidden = gen_entry(_pat('.*'), dirname, basename, offset)
    chain = gen_entry(_pat('*'), dirname, basename, offset), hidden

    entries = list(itertools.islice(itertools.chain(*chain), LIMIT))
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
        \$[A-Za-z0-9{}_]+/|

        # 'c:/'
        (?<![A-Za-z])[A-Za-z]:/|

        # 'dirname/'
        [@a-zA-Z0-9(){}+_\x80-\xff-\[\]]+/
        )+

        # Tail part
        (?:
        # any alphanumeric, symbol or space literal
        [/@a-zA-Z0-9(){}$ +_~.'"\x80-\xff-\[\]]|

        # skip any special symbols
        [^\x20-\x7E]|

        # backslash and 1 char after it
        \\.
        )*$""", re.U | re.X)

    # Ingore whitespace.
    ident = r"""[@a-zA-Z0-9(){}$+_~.'"\x80-\xff\u4e00-\u9fff\[\]-]*"""

    def match(self, input_data):
        if Completor.get_option('filename_completion_in_only_comment'):
            if self.is_comment_or_string():
                return bool(self.trigger.search(input_data))
            return False
        else:
            return bool(self.trigger.search(input_data))

    def _path(self, base):
        pat = list(PAT.finditer(base))
        if pat:
            base = base[pat[-1].end():]

        try:
            match = self.trigger.search(base)
        except TypeError as e:
            logger.exception(e)
            match = None

        if not match:
            logger.info('no matches')
            return

        if match.group()[-1] == ' ':
            return
        return match.group()

    def parse(self, base):
        """
        :param base: type unicode
        """
        logger.info('start filename parse: %s', base)
        path = self._path(base)
        if path is None:
            return []

        offset = self.start_column()
        try:
            if START_NO_DIRNAME.search(path):
                items = find(self.current_directory, path, offset)
            else:
                items = find(self.current_directory, './' + path, offset)
        except Exception as e:
            logger.exception(e)
            return []
        logger.info('completions: %s', items)
        return [item[0] for item in items]
