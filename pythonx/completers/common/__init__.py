# -*- coding: utf-8 -*-

import completor
import itertools
import re

from completor.compat import text_type

from .filename import Filename  # noqa
from .buffer import Buffer  # noqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass

word = re.compile(r'[^\W\d]\w*$', re.U)


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    hooks = ['ultisnips', 'buffer']

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

        if len(base) < self.get_option('min_chars'):
            return []

        return list(itertools.chain(
            *[self.completions(n, base) for n in self.hooks]))
