# -*- coding: utf-8 -*-

import completor

from .filename import Filename  # noqa
from .buffer import Buffer  # noqa
from .omni import Omni  # noqa

try:
    from UltiSnips import UltiSnips_Manager  # noqa
    from .ultisnips import Ultisnips  # noqa
except ImportError:
    pass


space = (' ', '\r', '\t', '\n')


class Other(completor.Completor):
    filetype = 'other'
    sync = True

    def parse(self, base):
        if base.endswith(space):
            return []

        completions = []
        ultisnips = completor.get('ultisnips')
        if ultisnips:
            completions.extend(ultisnips.parse(base))

        buffer = completor.get('buffer')
        if buffer:
            completions.extend(buffer.parse(base))
        return completions
