# -*- coding: utf-8 -*-

import completor
import itertools
import re

from .filename import Filename  # noqa
from .buffer import Buffer  # noqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass

word = re.compile(r'[^\W\d]{3,}\w*$', re.U)


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    def get_completions(self, completer, base):
        com = completor.get(completer)
        if not com:
            return []
        com.ft = self.ft
        if com.disabled:
            return []
        return com.parse(base)

    def parse(self, base):
        match = word.search(base)
        if not match:
            return []
        base = match.group()

        return list(itertools.chain(
            *[self.get_completions(n, base) for n in ('ultisnips', 'buffer')]))
