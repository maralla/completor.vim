# -*- coding: utf-8 -*-

import completor
import itertools
import re
import vim

from completor.compat import text_type
from .utils import subseq_binary

word = re.compile(r'[^\W\d]\w*$', re.U)


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    def too_short(self, base):
        return len(base) < self.get_option('completor_min_chars')

    def format_cmd(self):
        return [subseq_binary()]

    def query(self):
        match = word.search(self.input_data)
        if not match:
            return ''
        base = match.group()
        if self.too_short(base):
            return ''
        self.base = base
        return ''.join(['BUF', base])

    def add(self):
        name = vim.current.buffer.name
        return ''.join(['ADDFIL', name])

    def request(self, action='query'):
        self.base = ''
        if action == 'query':
            return self.query()
        elif action == 'add':
            return self.add()
        return ''

    def completions(self, completer, base):
        com = completor.get(completer)
        if not com:
            return []
        com.ft = self.ft
        if com.disabled:
            return []
        return com.parse(base)

    def daemon_response(self, items):
        res = []
        if self.base:
            ulti = completor.get('ultisnips')
            if ulti and not ulti.disabled:
                ulti.ft = self.ft
                res.extend(ulti.parse(self.base))

        for item in items:
            if not item or item.startswith(b'Err:'):
                continue
            res.extend(({'word': e, 'menu': '[ID]'}
                        for e in item.split(b'||')))
        return res

    def parse(self, base):
        if self.daemon:
            return self.daemon_response(base)

        if not isinstance(base, text_type):
            return []
        match = word.search(base)
        if not match:
            return []
        base = match.group()

        if self.too_short(base):
            return []

        return list(itertools.chain(
            *[self.completions(n, base) for n in ('ultisnips', 'buffer')]))
