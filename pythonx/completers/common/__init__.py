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


class Common(completor.Completor):
    filetype = 'common'
    sync = True

    def parse(self, base):
        if base.endswith(space):
            return []

        filename = completor.get('filename')
        if filename and not filename.disabled:
            filenames = filename.parse(base)
            if filenames:
                return filenames

        completions = []
        ultisnips = completor.get('ultisnips')
        if ultisnips and not ultisnips.disabled:
            completions.extend(ultisnips.parse(base))

        buffer = completor.get('buffer')
        if buffer and not buffer.disabled:
            completions.extend(buffer.parse(base))
        return completions
