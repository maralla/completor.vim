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

    # For extensions.
    hooks = ['ultisnips', 'buffer', 'filename']

    def __init__(self, *args, **kwargs):
        completor.Completor.__init__(self, *args, **kwargs)
        self._start_column = None

    @classmethod
    def is_common(cls, comp):
        return isinstance(comp, (cls, Buffer))

    def completions(self, completer, base):
        com = completor.get(completer)
        if not com:
            return []
        self.copy_to(com)
        if com.disabled:
            return []
        func = getattr(com, 'parse', None)
        try:
            items = (func or com.on_complete)(base)
            if items and 'offset' not in items[0]:
                if self._start_column is None:
                    self._start_column = self.start_column()
                items['offset'] = self._start_column
            return items
        except AttributeError:
            return []

    def parse(self, base):
        if not isinstance(base, text_type):
            return []
        try:
            return list(itertools.chain(
                *[self.completions(n, base) for n in self.hooks]))
        finally:
            self._start_column = None
