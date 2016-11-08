# -*- coding: utf-8 -*-

import itertools
import re
import completor
from completor.compat import text_type

word = re.compile(r'[^\W\d]\w*$', re.U)


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    def completions(self, completer, base):
        com = completor.get(completer)
        if not com:
            return []
        com.ft = self.ft
        if com.disabled:
            return []
        return com.parse(base)

    def parse(self, base):
        if not isinstance(base, text_type):
            return []
        match = word.search(base)
        if not match:
            return []
        base = match.group()

        if len(base) < self.get_option('completor_min_chars'):
            return []

        return list(itertools.chain(
            *[self.completions(n, base) for n in ('ultisnips', 'buffer')]))
