# -*- coding: utf-8 -*-
# flake8: noqa

import completor

from .filename import Filename
from .buffer import Buffer
from .omni import Omni

try:
    from UltiSnips import UltiSnips_Manager
    from .ultisnips import Ultisnips
except ImportError:
    pass


class Other(completor.Completor):
    filetype = 'other'
    sync = True

    def parse(self, base):
        completions = []
        ultisnips = completor.get('ultisnips')
        if ultisnips:
            completions.extend(ultisnips.parse(base))

        buffer = completor.get('buffer')
        if buffer:
            completions.extend(buffer.parse(base))
        return completions
