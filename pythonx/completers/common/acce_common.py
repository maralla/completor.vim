# -*- coding: utf-8 -*-

import vim
import re
import completor
from completor import Completor

from .utils import subseq_binary

word = re.compile(r'[^\W\d]\w*$', re.U)


class Common(Completor):
    filetype = 'common'
    daemon = True

    def format_cmd(self):
        return [subseq_binary()]

    def query(self):
        match = word.search(self.input_data)
        if not match:
            return ''
        base = match.group()
        if len(base) < self.get_option('completor_min_chars'):
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

    def parse(self, items):
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
