# -*- coding: utf-8 -*-

import re
import vim

from completor import Completor


LIMIT = 50
word = re.compile('\w+$')


def gen_tokens(base):
    for buffer in vim.buffers:
        if not buffer.valid:
            continue

        data = '\n'.join(buffer[:])
        for match in re.finditer('{}\w+'.format(base), data, re.M | re.I):
            yield match.group()


class Buffer(Completor):
    filetype = 'buffer'

    sync = True

    def parse(self, base):
        match = word.search(base)
        if not match:
            return []

        base = match.group()

        res = set()

        for token in gen_tokens(base):
            res.add(token)
            if len(res) >= LIMIT:
                break

        return [{'word': token, 'menu': '[ID]'} for token in res]
