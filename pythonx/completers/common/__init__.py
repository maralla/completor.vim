# -*- coding: utf-8 -*-

import logging
import completor
import itertools
import re

from completor.compat import text_type

from .filename import Filename  # noqa
from .neoinclude import Neoinclude  # noqa
from .buffer import Buffer  # naoqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass

word = re.compile(r'[^\W\d]\w*$', re.U)
logger = logging.getLogger('completor')


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    hooks = ['ultisnips', 'buffer', 'filename']

    @classmethod
    def is_common(cls, comp):
        return isinstance(comp, (cls, Buffer))

    def completions(self, completer, base):
        com = completor.get(completer)
        if not com:
            return []
        com.ft = self.ft
        com.input_data = self.input_data
        if com.disabled:
            return []
        func = getattr(com, 'parse', None)
        try:
            return (func or com.on_complete)(base)
        except AttributeError as e:
            return []

    def parse(self, base):
        if not isinstance(base, text_type):
            return []
        # match = word.search(base)
        # if not match:
        #     return []
        # base = match.group()

        # if len(base) < self.get_option('min_chars'):
        #     return []

        return list(itertools.chain(
            *[self.completions(n, base) for n in self.hooks]))
